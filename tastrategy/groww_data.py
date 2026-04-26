import os
import sys
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

API_TOKEN = os.getenv("GROWW_ACCESS_TOKEN")

# ── Lazy-init Groww client (graceful if package not installed) ────────────────
groww = None
_init_error = None

try:
    from growwapi import GrowwAPI
    if API_TOKEN:
        groww = GrowwAPI(API_TOKEN)
    else:
        _init_error = "GROWW_ACCESS_TOKEN is not set in .env"
except ImportError:
    _init_error = "growwapi package not installed — run: pip install growwapi"
except Exception as e:
    _init_error = f"Groww API init failed: {e}"

if _init_error:
    print(f"WARNING: {_init_error}", file=sys.stderr)


# ── Interval config ───────────────────────────────────────────────────────────
_INTERVAL_MINUTES = {
    "1m":     1,
    "5m":     5,
    "10m":    10,
    "15m":    15,
    "30m":    30,
    "1h":     60,
    "4h":     240,
    "1d":     1440,
    "day":    1440,
    "1w":     10080,
    "weekly": 10080,
}

# Maximum calendar days the API supports per interval
_MAX_CALENDAR_DAYS = {
    1:     7,
    5:     15,
    10:    30,
    15:    60,
    30:    90,
    60:    150,
    240:   365,
    1440:  1080,
    10080: 3650,
}

# Minimum candles we need — we always request enough calendar days to cover 220 candles.
# Approximate trading-days/candles-per-calendar-day for each interval:
_CANDLES_PER_CAL_DAY = {
    1:     390,    # 1m  — ~6.5 trading hours × 60m
    5:     78,     # 5m
    10:    39,     # 10m
    15:    26,     # 15m
    30:    13,     # 30m
    60:    6.5,    # 1h
    240:   1.625,  # 4h
    1440:  1,      # 1d
    10080: 1/5,    # 1w  (1 candle per 5 calendar days)
}

MIN_CANDLES = 220   # always fetch enough for at least this many candles


def _calendar_days_for_candles(interval_minutes: int, n_candles: int) -> int:
    """Return calendar days needed to get at least n_candles of data."""
    rate = _CANDLES_PER_CAL_DAY.get(interval_minutes, 1)
    if rate <= 0:
        rate = 1
    # add 40% buffer for weekends / holidays
    needed = int((n_candles / rate) * 1.4) + 5
    return max(needed, 10)


def fetch_ohlc(symbol: str, interval: str = "day", days: int = 220) -> pd.DataFrame | None:
    """
    Fetch OHLC data from Groww API.

    Always retrieves enough calendar days to cover at least MIN_CANDLES (220) candles,
    regardless of the `days` argument (which is a legacy param and still respected as a
    minimum).  If the API call fails for any reason the function returns None and logs the
    reason to stderr — it never raises.

    Returns a DataFrame with columns: Date, Open, High, Low, Close, Volume
    or None on failure.
    """
    if groww is None:
        print(f"ERROR: {symbol} — Groww client not available: {_init_error}", file=sys.stderr)
        return None

    interval_minutes = _INTERVAL_MINUTES.get(interval, 1440)

    # We want at least MIN_CANDLES candles, but honour a larger `days` request too
    days_for_min_candles = _calendar_days_for_candles(interval_minutes, MIN_CANDLES)
    requested_calendar_days = max(days, days_for_min_candles)

    # Cap at API maximum for this interval
    max_allowed = _MAX_CALENDAR_DAYS.get(interval_minutes, 1080)
    adjusted_days = min(requested_calendar_days, max_allowed)

    end_time   = datetime.now()
    start_time = end_time - timedelta(days=adjusted_days)

    try:
        response = groww.get_historical_candle_data(
            trading_symbol=symbol,
            exchange=groww.EXCHANGE_NSE,
            segment=groww.SEGMENT_CASH,
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            interval_in_minutes=interval_minutes,
        )
    except Exception as e:
        print(f"ERROR: {symbol} [{interval}] — API call failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None

    if not response:
        print(f"WARNING: {symbol} [{interval}] — Empty response from API", file=sys.stderr)
        return None

    candles = response.get("candles")
    if not candles:
        print(f"WARNING: {symbol} [{interval}] — 'candles' key missing or empty in response", file=sys.stderr)
        return None

    try:
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["Date"]   = pd.to_datetime(df["timestamp"], unit="s")
        df = df[["Date", "open", "high", "low", "close", "volume"]]
        df.columns   = ["Date", "Open", "High", "Low", "Close", "Volume"]
        df = df.sort_values("Date").reset_index(drop=True)

        # Drop rows with all-zero OHLC (bad data guard)
        df = df[~((df["Open"] == 0) & (df["High"] == 0) & (df["Low"] == 0) & (df["Close"] == 0))]

        # Drop NaN price rows
        df = df.dropna(subset=["Open", "High", "Low", "Close"])

        if df.empty:
            print(f"WARNING: {symbol} [{interval}] — DataFrame empty after cleaning", file=sys.stderr)
            return None

        n = len(df)
        print(
            f"✓ {symbol} [{interval}]: {n} candles fetched "
            f"(requested {adjusted_days}d / target ≥{MIN_CANDLES} candles)",
            file=sys.stderr
        )

        if n < 50:
            print(
                f"WARNING: {symbol} [{interval}] — Only {n} candles; "
                f"indicators may be unreliable (need ≥50)",
                file=sys.stderr
            )

        return df

    except Exception as e:
        print(f"ERROR: {symbol} [{interval}] — DataFrame construction failed: {e}", file=sys.stderr)
        return None