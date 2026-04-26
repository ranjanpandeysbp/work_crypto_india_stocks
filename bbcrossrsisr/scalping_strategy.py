import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta, timezone
import time
import logging
import sys
import io

# ─── Logging Configuration ──────────────────────────────────────────────────────
# Ensure stdout/stderr use UTF-8 on Windows to avoid UnicodeEncodeError with emojis
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scalping_strategy.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MTF Scalping Strategy",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Bebas+Neue&display=swap');

:root {
    --bg: #0a0c10;
    --surface: #111318;
    --surface2: #1a1d24;
    --border: #252830;
    --accent: #00d4ff;
    --accent2: #ff9500;
    --green: #00ff88;
    --red: #ff3860;
    --yellow: #ffd600;
    --purple: #bd93f9;
    --text: #e0e4ef;
    --muted: #6b7280;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border);
}

h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px; }

.stTextInput > div > div > input,
.stMultiSelect > div > div,
.stSelectbox > div > div {
    background-color: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), #0087a8) !important;
    color: #000 !important;
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 2px !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 10px 30px !important;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0,212,255,0.4) !important;
}

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
}
.metric-card .label { color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
.metric-card .value { font-size: 15px; font-weight: 700; margin-top: 2px; }

.bullish { color: var(--green) !important; }
.bearish { color: var(--red) !important; }
.neutral { color: var(--yellow) !important; }
.accent  { color: var(--accent) !important; }
.purple  { color: var(--purple) !important; }

.tf-header {
    background: linear-gradient(90deg, var(--surface2), var(--surface));
    border-left: 3px solid var(--accent);
    border-radius: 0 6px 6px 0;
    padding: 10px 18px;
    margin: 20px 0 10px 0;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 22px;
    letter-spacing: 3px;
    color: var(--accent);
}
.tf-header-india {
    border-left-color: var(--accent2) !important;
    color: var(--accent2) !important;
}

.signal-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    margin: 2px;
}
.pill-bull { background: rgba(0,255,136,0.15); border: 1px solid var(--green); color: var(--green); }
.pill-bear { background: rgba(255,56,96,0.15);  border: 1px solid var(--red);   color: var(--red); }
.pill-neu  { background: rgba(255,214,0,0.15);  border: 1px solid var(--yellow);color: var(--yellow); }

.ticker-badge {
    background: var(--surface2);
    border: 1px solid var(--accent);
    color: var(--accent);
    padding: 4px 14px;
    border-radius: 3px;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 20px;
    letter-spacing: 2px;
    display: inline-block;
    margin: 4px;
}
.ticker-badge-india {
    border-color: var(--accent2) !important;
    color: var(--accent2) !important;
}

.source-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 3px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    letter-spacing: 1px;
    margin-left: 8px;
    vertical-align: middle;
}
.badge-crypto { background: rgba(0,212,255,0.12); border: 1px solid var(--accent);  color: var(--accent); }
.badge-india  { background: rgba(255,149,0,0.12);  border: 1px solid var(--accent2); color: var(--accent2); }

.error-box {
    background: rgba(255,56,96,0.1);
    border: 1px solid var(--red);
    border-radius: 6px;
    padding: 12px 16px;
    color: var(--red);
    font-size: 12px;
}
.info-box {
    background: rgba(255,149,0,0.07);
    border: 1px solid rgba(255,149,0,0.3);
    border-radius: 6px;
    padding: 10px 14px;
    color: var(--accent2);
    font-size: 11px;
    margin: 6px 0;
    line-height: 1.6;
}

[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── API Constants ───────────────────────────────────────────────────────────

DELTA_BASE = "https://api.india.delta.exchange"
GROWW_BASE = "https://api.groww.in"

# Crypto TF map: key → (delta_resolution, seconds_per_candle)
TF_CRYPTO = {
    "1m":  ("1m",   60),
    "3m":  ("3m",   180),
    "5m":  ("5m",   300),
    "15m": ("15m",  900),
    "30m": ("30m",  1800),
    "1h":  ("1h",   3600),
    "2h":  ("2h",   7200),
    "4h":  ("4h",   14400),
    "1d":  ("1d",   86400),
}

# India TF map: key → (groww_minutes, max_fetch_days, seconds_per_candle)
TF_INDIA = {
    "1m":  (1,    7,    60),
    "5m":  (5,    15,   300),
    "10m": (10,   30,   600),
    "15m": (15,   60,   900),
    "30m": (30,   90,   1800),
    "1h":  (60,   150,  3600),
    "4h":  (240,  300,  14400),
    "1d":  (1440, 1080, 86400),
}

NIFTY_50 = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "INFY", "SBIN", "LICI", "ITC", "HINDUNILVR",
    "LT", "BAJFINANCE", "ADANIENT", "SUNPHARMA", "M&M", "ADANIPORTS", "MARUTI", "KOTAKBANK", "HCLTECH", "TITAN",
    "AXISBANK", "ULTRACEMCO", "NTPC", "ONGC", "ASIANPAINT", "COALINDIA", "TATASTEEL", "ADANIPOWER", "POWERGRID", "ADANIGREEN",
    "JSWSTEEL", "ADANITRANS", "SBILIFE", "GRASIM", "HINDALCO", "BAJAJFINSV", "NESTLEIND", "BAJAJ-AUTO", "BRITANNIA", "EICHERMOT",
    "TECHM", "WIPRO", "INDUSINDBK", "CIPLA", "APOLLOHOSP", "HEROMOTOCO", "DIVISLAB", "LTIM", "BPCL", "TATAMOTORS"
]

NIFTY_MIDCAP_150 = [
    "PFC", "RECLTD", "TVSMOTOR", "LUPIN", "MRF", "AUROPHARMA", "ASHOKLEY", "IDFCFIRSTB", "ASTRAL", "CUMMINSIND",
    "VOLTAS", "OBEROIRLTY", "JUBLFOOD", "IDEA", "BIOCON", "BANDHANBNK", "ZEEL", "PAYTM", "ZOMATO", "NYKAA",
    "POLICYBZR", "MOTHERSON", "BHEL", "SAIL", "CONCOR", "ABCAPITAL", "ESCORTS", "COROMANDEL", "MFSL", "DALBHARAT"
]

NIFTY_SMALLCAP_250 = [
    "SUZLON", "IRFC", "RVNL", "MAZDOCK", "KALYANKJIL", "ANGELONE", "CDSL", "BSE", "MCX", "RADICO",
    "CEATLTD", "BLS", "LATENTVIEW", "CYIENT", "ZENSARTECH", "SONACOMS", "CAMS", "HAPPSTMNDS", "GLENMARK", "JBCHEPHARM",
    "GRANULES", "NATCOPHARM", "UCOBANK", "CENTRALBK", "IOB", "MAHABANK", "J&KBANK", "CSBBANK", "KARURVYSYA", "SOUTHBANK"
]

NIFTY_500 = list(set(NIFTY_50 + NIFTY_MIDCAP_150 + NIFTY_SMALLCAP_250))

# ─── Data Fetchers ────────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def fetch_delta_ohlcv(symbol: str, resolution: str, limit: int = 300) -> pd.DataFrame:
    """
    Fetch OHLCV from Delta Exchange public REST API.
    
    Implements fallback strategies:
    1. Try requested timeframe with current time window
    2. If empty, try with extended time window (older data)
    3. If still empty, try with larger timeframe
    """
    try:
        secs     = TF_CRYPTO.get(resolution)
        if secs is None:
            error_msg = f"Invalid resolution '{resolution}' for Delta Exchange. Valid: {list(TF_CRYPTO.keys())}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        secs = secs[1]
        logger.info(f"Fetching Delta Exchange data: symbol={symbol}, resolution={resolution}, limit={limit}")

        # ─── Strategy 1: Try current timeframe with recent data ───
        end_ts   = int(datetime.now(timezone.utc).timestamp())
        start_ts = end_ts - secs * limit

        logger.debug(f"Strategy 1: Recent data fetch - {symbol} [{resolution}]")
        delta_headers = {"Accept": "application/json"}
        r = requests.get(
            f"{DELTA_BASE}/v2/history/candles",
            params={"resolution": resolution, "symbol": symbol.upper(),
                    "start": start_ts, "end": end_ts},
            headers=delta_headers,
            timeout=10,
        )
        
        if r.status_code != 200:
            error_msg = f"Delta API HTTP {r.status_code}: {r.text[:150]}"
            logger.error(error_msg)
            r.raise_for_status()
        
        data = r.json()
        logger.debug(f"Strategy 1 result: success={data.get('success')}, count={len(data.get('result', []))}")
        
        if data.get("success") is False:
            error_msg = f"Delta API returned success=false: {data.get('message', 'Unknown error')}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        result = data.get("result", [])
        
        # ─── Strategy 2: If empty, try with older time window (go back further) ───
        if not result:
            logger.debug(f"Strategy 2: Empty result, trying older time window - {symbol} [{resolution}]")
            
            # Try going back 7 days instead of just the limit
            older_end_ts = int((datetime.now(timezone.utc) - timedelta(hours=12)).timestamp())
            older_start_ts = older_end_ts - secs * min(limit * 2, 1000)  # Try up to 1000 candles going back
            
            r = requests.get(
                f"{DELTA_BASE}/v2/history/candles",
                params={"resolution": resolution, "symbol": symbol.upper(),
                        "start": older_start_ts, "end": older_end_ts},
                headers=delta_headers,
                timeout=10,
            )
            
            data = r.json()
            result = data.get("result", [])
            logger.debug(f"Strategy 2 result: count={len(result)}")
        
        # ─── Strategy 3: If still empty, try a larger timeframe ───
        if not result and resolution != "1d":
            # Map to larger timeframe
            fallback_tfs = {
                "1m": "5m", "3m": "5m", "5m": "15m",
                "15m": "1h", "30m": "1h", "1h": "4h",
                "2h": "4h", "4h": "1d"
            }
            
            if resolution in fallback_tfs:
                fallback_tf = fallback_tfs[resolution]
                fallback_secs = TF_CRYPTO.get(fallback_tf)[1]
                
                logger.debug(f"Strategy 3: Trying larger timeframe - {symbol} [{fallback_tf}] (fallback from [{resolution}])")
                
                end_ts = int(datetime.now(timezone.utc).timestamp())
                start_ts = end_ts - fallback_secs * limit
                
                r = requests.get(
                    f"{DELTA_BASE}/v2/history/candles",
                    params={"resolution": fallback_tf, "symbol": symbol.upper(),
                            "start": start_ts, "end": end_ts},
                    headers=delta_headers,
                    timeout=10,
                )
                
                data = r.json()
                result = data.get("result", [])
                logger.debug(f"Strategy 3 result: count={len(result)}, using timeframe={fallback_tf}")
                
                if result:
                    logger.warning(f"Using fallback timeframe {fallback_tf} instead of {resolution} for {symbol}")

        if not result:
            # All strategies exhausted - provide helpful error
            hint = (
                f"Unable to fetch data for {symbol} with {resolution} timeframe. "
                f"The ticker may not exist on Delta Exchange, or no historical data is available. "
                f"Try: (1) Different timeframe (use 1h or 1d), "
                f"(2) Try 'Groww' for Indian stocks, "
                f"(3) Check https://docs.delta.exchange for supported instruments"
            )
            logger.error(f"All fetch strategies exhausted for {symbol} [{resolution}]")
            raise ValueError(hint)

        df = pd.DataFrame(result, columns=["time","open","high","low","close","volume"])
        
        if df.empty:
            error_msg = f"DataFrame is empty after parsing for {symbol} [{resolution}]"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        df = df.sort_values("time").reset_index(drop=True)
        for c in ["open","high","low","close","volume"]:
            df[c] = df[c].astype(float)
        
        logger.info(f"✅ Successfully fetched {len(df)} candles for {symbol}")
        return df

    except requests.exceptions.Timeout as e:
        error_msg = f"Request timeout while fetching {symbol} from Delta Exchange: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error to Delta Exchange: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    except Exception as e:
        error_msg = f"Unexpected error fetching {symbol} [{resolution}]: {str(e)}"
        logger.error(error_msg)
        raise


@st.cache_data(ttl=60, show_spinner=False)
def fetch_groww_ohlcv(symbol: str, exchange: str, tf_key: str,
                      api_token: str, limit: int = 300) -> pd.DataFrame:
    """
    Fetch OHLCV from Groww Historical Candle API.

    Tries the newer /v1/historical/candles endpoint (backtesting API),
    falls back to the legacy /v1/historical/candle/range endpoint.
    Both require a valid Groww Trade API Bearer token.

    Groww supported intervals: 1, 5, 10, 60, 240, 1440 minutes.
    Max window per request varies by interval (see TF_INDIA).
    """
    try:
        # Validate token
        if not api_token or not api_token.strip():
            error_msg = "Groww Bearer token is missing or empty. Get one from groww.in/trade-api"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate timeframe
        if tf_key not in TF_INDIA:
            error_msg = f"Invalid timeframe '{tf_key}' for Groww. Valid: {list(TF_INDIA.keys())}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        minutes, max_days, _ = TF_INDIA[tf_key]

        now          = datetime.now()
        # Account for limited market hours in India (approx 6.25h/24h)
        # We multiply the lookback to ensure we get enough calendar days for the requested candle limit
        lookback_multiplier = 4 if tf_key != "1d" else 1.6
        lookback_min = min(int(minutes * limit * lookback_multiplier), max_days * 24 * 60)
        start_dt     = now - timedelta(minutes=lookback_min)

        # Format: "YYYY-MM-DD HH:MM:SS"
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str   = now.strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Fetching Groww data: symbol={symbol}, exchange={exchange}, tf={tf_key}, limit={limit}")

        headers = {
            "Accept":        "application/json",
            "Authorization": f"Bearer {api_token.strip()}",
            "X-API-VERSION": "1.0",
        }

        # ── Attempt 1: new backtesting endpoint ──────────────────────────────
        # Groww symbol format: "NSE-RELIANCE", "BSE-TCS" etc.
        groww_symbol = f"{exchange.upper()}-{symbol.upper()}"
        
        logger.info(f"Attempt 1: Trying new backtesting endpoint with symbol {groww_symbol}")
        try:
            r1 = requests.get(
                f"{GROWW_BASE}/v1/historical/candles",
                headers=headers,
                params={
                    "exchange":       exchange.upper(),
                    "segment":        "CASH",
                    "groww_symbol":   groww_symbol,
                    "start_time":     start_str,
                    "end_time":       end_str,
                    "candle_interval": f"{minutes}minute",
                },
                timeout=15,
            )
            
            if r1.status_code == 200:
                payload = r1.json().get("payload", {})
                candles = payload.get("candles", [])
                if candles:
                    logger.info(f"✅ Successfully fetched {len(candles)} candles via new endpoint")
                    return _parse_groww_candles(candles)
                else:
                    logger.warning(f"New endpoint returned empty candles for {symbol}")
            
            elif r1.status_code == 401:
                logger.warning(f"Attempt 1: Groww 401 (Unauthorized). Token may be invalid or expired. Trying legacy endpoint...")
            
            elif r1.status_code == 403:
                logger.warning(f"Attempt 1: Groww 403 (Forbidden). Backtesting API subscription may be inactive. Falling back to legacy endpoint...")
            
            elif r1.status_code == 404:
                logger.warning(f"Symbol {groww_symbol} not found on new endpoint (404), trying legacy endpoint")
            
            else:
                logger.warning(f"New endpoint returned status {r1.status_code}, falling back to legacy")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"New endpoint request failed: {str(e)}, falling back to legacy")

        # ── Attempt 2: legacy range endpoint (still active as of 2025) ───────
        logger.info(f"Attempt 2: Trying legacy candle/range endpoint for {symbol}")
        
        try:
            r2 = requests.get(
                f"{GROWW_BASE}/v1/historical/candle/range",
                headers=headers,
                params={
                    "exchange":            exchange.upper(),
                    "segment":             "CASH",
                    "trading_symbol":      symbol.upper(),
                    "start_time":          start_str,
                    "end_time":            end_str,
                    "interval_in_minutes": str(minutes),
                },
                timeout=15,
            )

            # Check for HTTP errors
            if r2.status_code == 401:
                error_msg = f"Groww authentication failed (401). Bearer token is invalid or expired"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            elif r2.status_code == 403:
                error_msg = f"Groww permission denied (403). Ensure Trade API subscription is active"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            elif r2.status_code == 404:
                error_msg = f"Symbol '{symbol}' not found on {exchange}. Check spelling and exchange selection"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            elif r2.status_code != 200:
                error_msg = f"Groww API HTTP {r2.status_code}: {r2.text[:150]}"
                logger.error(error_msg)
                r2.raise_for_status()

            body = r2.json()

            # Check response status
            if body.get("status") != "SUCCESS":
                error_msg = f"Groww returned status '{body.get('status')}': {body.get('message', 'No message')}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            candles = body.get("payload", {}).get("candles", [])
            
            if not candles:
                error_msg = (
                    f"No candle data returned for {symbol} on {exchange} [{tf_key}]. "
                    "Market may be closed or symbol may have no recent data."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"✅ Successfully fetched {len(candles)} candles via legacy endpoint")
            return _parse_groww_candles(candles)

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout from Groww API (legacy endpoint): {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except requests.exceptions.RequestException as e:
            # Fallback for 4h if it fails with 400 or other request errors
            if tf_key == "4h":
                logger.warning(f"Native 4h fetch failed for {symbol}. Attempting 1h-to-4h resampling...")
                try:
                    df_1h = fetch_groww_ohlcv(symbol, "1h", limit * 4, exchange, api_token)
                    if not df_1h.empty:
                        df_1h['time_dt'] = pd.to_datetime(df_1h['time'], unit='s')
                        df_1h.set_index('time_dt', inplace=True)
                        resampled = df_1h.resample('4H').agg({
                            'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                        }).dropna()
                        resampled.reset_index(inplace=True)
                        resampled['time'] = resampled['time_dt'].view('int64') // 10**9
                        logger.info(f"✅ Successfully resampled 1h to 4h for {symbol} ({len(resampled)} candles)")
                        return resampled
                except: pass
            
            error_msg = f"Groww API Request Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error to Groww API: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    except ValueError:
        raise  # Re-raise ValueError as is
    except Exception as e:
        error_msg = f"Unexpected error fetching {symbol} from Groww: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def _parse_groww_candles(candles: list) -> pd.DataFrame:
    """Normalise Groww candle arrays → clean DataFrame."""
    if not candles:
        error_msg = "Candles list is empty"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        rows = []
        for idx, c in enumerate(candles):
            try:
                ts = c[0]
                if isinstance(ts, str):
                    # ISO format: "2025-09-24T10:30:00"
                    try:
                        ts = int(datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").timestamp())
                    except Exception as e:
                        logger.warning(f"Failed to parse timestamp at index {idx}: {c[0]}. Using 0")
                        ts = 0
                
                # Validate OHLCV values
                open_price = float(c[1]) if len(c) > 1 and c[1] is not None else 0
                high_price = float(c[2]) if len(c) > 2 and c[2] is not None else 0
                low_price = float(c[3]) if len(c) > 3 and c[3] is not None else 0
                close_price = float(c[4]) if len(c) > 4 and c[4] is not None else 0
                volume = float(c[5]) if len(c) > 5 and c[5] is not None else 0.0
                
                # Validation checks
                if high_price < low_price:
                    logger.warning(f"Invalid candle at index {idx}: high ({high_price}) < low ({low_price})")
                    high_price, low_price = max(high_price, low_price), min(high_price, low_price)
                
                rows.append({
                    "time":   int(ts),
                    "open":   open_price,
                    "high":   high_price,
                    "low":    low_price,
                    "close":  close_price,
                    "volume": volume,
                })
            except Exception as e:
                logger.error(f"Error parsing candle at index {idx}: {c} - {str(e)}")
                continue
        
        if not rows:
            error_msg = "No valid candles parsed from Groww response"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
        logger.info(f"✅ Parsed {len(df)} candles from Groww response")
        return df
        
    except Exception as e:
        logger.error(f"Unexpected error fetching Groww candles: {str(e)}")
        raise ValueError(f"Groww error: {str(e)}")

def detect_patterns(df):
    """
    Detect common candlestick and chart patterns.
    Returns: (list of bullish patterns, list of bearish patterns)
    """
    bullish = []
    bearish = []
    
    if len(df) < 5:
        return bullish, bearish
        
    c = df.iloc[-1]
    p = df.iloc[-2]
    p2 = df.iloc[-3]
    
    # 1. Candlestick Patterns
    body = abs(c['close'] - c['open'])
    p_body = abs(p['close'] - p['open'])
    range_val = c['high'] - c['low']
    upper_wick = c['high'] - max(c['close'], c['open'])
    lower_wick = min(c['close'], c['open']) - c['low']
    
    # Doji
    if body < (range_val * 0.1) and range_val > 0:
        bullish.append("Doji (Indecision)")
        
    # Hammer (Bullish)
    if lower_wick > (2 * body) and upper_wick < (0.2 * body) and body > 0:
        bullish.append("Hammer (Bullish Reversal)")
        
    # Shooting Star (Bearish)
    if upper_wick > (2 * body) and lower_wick < (0.2 * body) and body > 0:
        bearish.append("Shooting Star (Bearish Reversal)")
        
    # Bullish Engulfing
    if p['close'] < p['open'] and c['close'] > c['open'] and \
       c['close'] >= p['open'] and c['open'] <= p['close']:
        bullish.append("Bullish Engulfing")
        
    # Bearish Engulfing
    if p['close'] > p['open'] and c['close'] < c['open'] and \
       c['close'] <= p['open'] and c['open'] >= p['close']:
        bearish.append("Bearish Engulfing")

    # Morning Star (Bullish)
    if p2['close'] < p2['open'] and p_body < (abs(p2['close']-p2['open'])*0.3) and \
       c['close'] > c['open'] and c['close'] > (p2['open'] + p2['close'])/2:
        bullish.append("Morning Star")
        
    # Evening Star (Bearish)
    if p2['close'] > p2['open'] and p_body < (abs(p2['close']-p2['open'])*0.3) and \
       c['close'] < c['open'] and c['close'] < (p2['open'] + p2['close'])/2:
        bearish.append("Evening Star")

    # 2. Simple Chart Patterns (using last 20 candles)
    recent = df.iloc[-20:]
    highs = recent['high'].values
    lows = recent['low'].values
    
    # Double Bottom (simplified)
    # Find two local lows within 2% of each other
    if len(lows) >= 10:
        l1, l2 = sorted(lows)[:2]
        if abs(l1 - l2) / l1 < 0.005 and c['close'] > (l1 * 1.01):
            bullish.append("Double Bottom (Potential)")
            
    # Double Top (simplified)
    if len(highs) >= 10:
        h1, h2 = sorted(highs, reverse=True)[:2]
        if abs(h1 - h2) / h1 < 0.005 and c['close'] < (h1 * 0.99):
            bearish.append("Double Top (Potential)")

    return bullish, bearish

@st.cache_data(ttl=30)
def get_coindcx_gainers():
    """Fetch and filter CoinDCX Futures gainers > 10%."""
    try:
        fetch_time = datetime.now().strftime("%H:%M:%S")
        url = "https://public.coindcx.com/market_data/v3/current_prices/futures/rt"
        resp = requests.get(url, timeout=10).json()
        prices = resp.get("prices", {})
        gainers = []
        for sym, data in prices.items():
            pc = data.get("pc", 0)
            if pc > 10:
                high_val = data.get("h", 0)
                last_val = data.get("ls", 0)
                
                # Calculate the 24h base price to find the high %
                # pc = (last / base - 1) * 100  =>  base = last / (1 + pc/100)
                if pc != -100 and last_val > 0:
                    base_price = last_val / (1 + pc / 100)
                    high_pc = ((high_val / base_price) - 1) * 100
                else:
                    high_pc = 0
                
                display_name = sym.replace("B-", "").replace("_", "")
                gainers.append({
                    "sym": sym, 
                    "label": f"{display_name} (Gain: {pc:.1f}% | High: {high_pc:.1f}%)"
                })
        return sorted(gainers, key=lambda x: x["label"]), fetch_time
    except Exception as e:
        logger.error(f"Error fetching CoinDCX gainers: {e}")
        return [], datetime.now().strftime("%H:%M:%S")

def analyze_pump_dump_candidates(mode="PUMP"):
    """
    Deep scan of CoinDCX tickers to find 'Pump' or 'Dump' candidates.
    mode: 'PUMP' or 'DUMP'
    """
    try:
        # Fetch current prices to get all symbols
        url_rt = "https://public.coindcx.com/market_data/v3/current_prices/futures/rt"
        resp_rt = requests.get(url_rt, timeout=10).json()
        prices = resp_rt.get("prices", {})
        
        # Sort by 24h gain and scan top 30 to keep it fast
        tickers = sorted(prices.keys(), key=lambda x: prices[x].get("pc", 0), reverse=(mode=="PUMP"))[:30]
        
        candidates = []
        for symbol in tickers:
            try:
                # Fetch context
                df = fetch_coindcx_ohlcv(symbol, "1h", limit=24) # 24h
                df_5m = fetch_coindcx_ohlcv(symbol, "5m", limit=24) # 2h
                
                if df_5m.empty or len(df_5m) < 20: continue
                
                price = df_5m.iloc[-1]['close']
                # Volume surging check
                vol_recent = df_5m['volume'].mean()
                vol_24h = df['volume'].mean()
                v_surge = vol_recent / vol_24h if vol_24h > 0 else 1.0
                
                st_sig, _ = supertrend(df_5m)
                vw = vwap(df_5m)
                rsi_val = rsi(df_5m['close']).iloc[-1]
                bull_p, bear_p = detect_patterns(df_5m)
                
                # S/R context
                sh, sl = df_5m['high'].max(), df_5m['low'].min()
                breakout = price > sh * 0.998
                breakdown = price < sl * 1.002
                
                prob = 40 # Base prob
                reasons = []
                
                if mode == "PUMP":
                    if v_surge > 1.3: prob += 15; reasons.append(f"Vol Surge {v_surge:.1f}x")
                    if st_sig.iloc[-1]: prob += 10; reasons.append("Supertrend Bullish")
                    if price > vw.iloc[-1]: prob += 10; reasons.append("Above VWAP")
                    if rsi_val > 65: prob += 10; reasons.append("Strong Momentum")
                    if bull_p: prob += 15; reasons.append("Bull Patterns")
                    if breakout: prob += 10; reasons.append("Resistance Breakout")
                    if bear_p: prob -= 20
                else: # DUMP
                    if v_surge > 1.3: prob += 15; reasons.append(f"Heavy Volume {v_surge:.1f}x")
                    if not st_sig.iloc[-1]: prob += 10; reasons.append("Supertrend Bearish")
                    if price < vw.iloc[-1]: prob += 10; reasons.append("Below VWAP")
                    if rsi_val < 35: prob += 10; reasons.append("Weak Momentum")
                    if bear_p: prob += 15; reasons.append("Bear Patterns")
                    if breakdown: prob += 10; reasons.append("Support Breakdown")
                    if bull_p: prob -= 20
                
                prob = max(10, min(98, prob))
                if prob >= 65:
                    display_name = symbol.replace("B-", "").replace("_", "")
                    candidates.append({
                        "Symbol": display_name,
                        "Prob": f"{prob}%",
                        "Signal": reasons[0] if reasons else "Multiple Factors",
                        "Score": prob
                    })
            except: continue
        return sorted(candidates, key=lambda x: x['Score'], reverse=True)
    except Exception as e:
        logger.error(f"Scanner error: {e}")
        return []

def analyze_groww_pump_dump_candidates(token, exchange="NSE", mode="PUMP", ticker_list=NIFTY_50):
    """
    Scan top Indian stocks for Pump/Dump potential.
    """
    if not token:
        return [{"Symbol": "TOKEN MISSING", "Prob": "0%", "Signal": "Enter Groww Token", "Score": 0}]
        
    candidates = []
    # Scan first 30 for speed
    for symbol in ticker_list[:30]:
        try:
            # Fetch context
            df = fetch_groww_ohlcv(symbol, exchange, "1h", token, limit=24) # 24h
            df_5m = fetch_groww_ohlcv(symbol, exchange, "5m", token, limit=24) # 2h
            
            if df_5m.empty or len(df_5m) < 20: continue
            
            price = df_5m.iloc[-1]['close']
            vol_recent = df_5m['volume'].mean()
            vol_24h = df['volume'].mean()
            v_surge = vol_recent / vol_24h if vol_24h > 0 else 1.0
            
            st_sig, _ = supertrend(df_5m)
            vw = vwap(df_5m)
            rsi_val = rsi(df_5m['close']).iloc[-1]
            bull_p, bear_p = detect_patterns(df_5m)
            
            prob = 35 # Base
            reasons = []
            
            if mode == "PUMP":
                if v_surge > 1.2: prob += 15; reasons.append(f"Vol Surge {v_surge:.1f}x")
                if st_sig.iloc[-1]: prob += 10; reasons.append("Supertrend Bullish")
                if price > vw.iloc[-1]: prob += 10; reasons.append("Above VWAP")
                if bull_p: prob += 15; reasons.append("Bull Patterns")
                if rsi_val > 60: prob += 10; reasons.append("Momentum")
                if bear_p: prob -= 20
            else: # DUMP
                if v_surge > 1.2: prob += 15; reasons.append(f"Heavy Volume {v_surge:.1f}x")
                if not st_sig.iloc[-1]: prob += 10; reasons.append("Supertrend Bearish")
                if price < vw.iloc[-1]: prob += 10; reasons.append("Below VWAP")
                if bear_p: prob += 15; reasons.append("Bear Patterns")
                if rsi_val < 40: prob += 10; reasons.append("Weakness")
                if bull_p: prob -= 20
                
            prob = max(10, min(95, prob))
            if prob >= 60:
                candidates.append({
                    "Symbol": symbol,
                    "Prob": f"{prob}%",
                    "Signal": reasons[0] if reasons else "Multiple Factors",
                    "Score": prob
                })
        except: continue
    return sorted(candidates, key=lambda x: x['Score'], reverse=True)

def fetch_coindcx_ohlcv(symbol, resolution, limit=1000):
    """
    Fetch OHLCV data from CoinDCX Futures API.
    Resolutions: '1', '5', '15', '60', '240', '1D'
    """
    url = "https://public.coindcx.com/market_data/candlesticks"
    
    # Map resolution
    res_map = {"1m": "1", "5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "1D"}
    res = res_map.get(resolution, resolution)
    
    # Calculate time range
    # 1000 candles * resolution in seconds
    res_sec = 60 if res == "1" else 300 if res == "5" else 900 if res == "15" else 3600 if res == "60" else 14400 if res == "240" else 86400
    lookback = limit * res_sec
    end = int(time.time())
    start = end - lookback
    
    params = {
        "pair": symbol,
        "from": start,
        "to": end,
        "resolution": res,
        "pcode": "f"
    }
    
    logger.info(f"Fetching CoinDCX Futures: {symbol} [{resolution}], limit={limit}")
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("s") != "ok":
            raise ValueError(f"CoinDCX API error: {data.get('message', 'Unknown error')}")
            
        candles = data.get("data", [])
        if not candles:
            return pd.DataFrame()
            
        rows = []
        for c in candles:
            rows.append({
                "time": int(c["time"] / 1000), # Convert ms to s
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
                "volume": float(c["volume"])
            })
            
        df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
        return df
    except Exception as e:
        logger.error(f"Error fetching CoinDCX candles: {str(e)}")
        return pd.DataFrame()

# ─── Technical Indicators ────────────────────────────────────────────────────

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def sma(series, period):
    return series.rolling(period).mean()

def bollinger_bands(close, period=20, std_dev=2):
    mid   = sma(close, period)
    std   = close.rolling(period).std()
    return mid + std_dev * std, mid, mid - std_dev * std

def rsi(close, period=14):
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    h, l, c = df["high"], df["low"], df["close"]
    tr1 = h - l
    tr2 = (h - c.shift()).abs()
    tr3 = (l - c.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def supertrend(df, period=10, multiplier=3):
    h, l, c = df["high"], df["low"], df["close"]
    avg_tr = atr(df, period)
    hl2 = (h + l) / 2
    up_lev = hl2 + (multiplier * avg_tr)
    dn_lev = hl2 - (multiplier * avg_tr)
    st = [True] * len(df)
    st_line = [0.0] * len(df)
    up_band = [0.0] * len(df)
    dn_band = [0.0] * len(df)
    for i in range(1, len(df)):
        up_band[i] = up_lev.iloc[i] if up_lev.iloc[i] < up_band[i-1] or c.iloc[i-1] > up_band[i-1] else up_band[i-1]
        dn_band[i] = dn_lev.iloc[i] if dn_lev.iloc[i] > dn_band[i-1] or c.iloc[i-1] < dn_band[i-1] else dn_band[i-1]
        if i == 1: st[i] = True
        else:
            if st[i-1] is True: st[i] = False if c.iloc[i] < dn_band[i] else True
            else: st[i] = True if c.iloc[i] > up_band[i] else False
        st_line[i] = dn_band[i] if st[i] else up_band[i]
    return pd.Series(st, index=df.index), pd.Series(st_line, index=df.index)

def vwap(df):
    cvp = (df["close"] * df["volume"]).cumsum()
    cv = df["volume"].cumsum()
    return cvp / cv

def pivot_levels(df, lookback=10):
    highs, lows, n = [], [], len(df)
    for i in range(lookback, n - lookback):
        wh = df["high"].iloc[i - lookback: i + lookback + 1]
        wl = df["low"].iloc[i - lookback: i + lookback + 1]
        if df["high"].iloc[i] == wh.max(): highs.append((i, df["high"].iloc[i]))
        if df["low"].iloc[i] == wl.min(): lows.append((i, df["low"].iloc[i]))
    return highs, lows

def fibonacci_levels(sh, sl):
    d = sh - sl
    return {f"{int(r*100)}%": sh - d * r for r in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]}

def analyse(df: pd.DataFrame, symbol: str, tf: str, ema_pairs=[(9, 21)], currency: str = "₹") -> dict:
    result = {"symbol": symbol, "tf": tf, "error": None, "currency": currency}

    try:
        # Validate DataFrame
        if df is None or df.empty:
            error_msg = f"Data is empty for {symbol} [{tf}]"
            logger.error(error_msg)
            result["error"] = error_msg
            return result

        # Dynamic minimum candles based on EMA pairs (e.g. 50/200 needs >200)
        max_ema = max([p[1] for p in ema_pairs]) if ema_pairs else 20
        min_ideal = max_ema + 10
        
        if len(df) < 50:
            error_msg = f"Insufficient data: Only {len(df)} candles fetched (need ≥50)."
            logger.warning(error_msg)
            result["error"] = error_msg
            return result
        
        if len(df) < min_ideal:
            st.warning(f"⚠️ **Limited Data**: Only {len(df)} candles fetched for {symbol} {tf}. "
                       f"Indicators like {max_ema} EMA may be less accurate (ideal ≥{min_ideal}).")

        close  = df["close"]
        high   = df["high"]
        low    = df["low"]
        volume = df["volume"]
        price  = close.iloc[-1]

        # ── EMA Crossovers ────────────────────────────────────────────────
        try:
            e200 = ema(close, 200)
            ema_signals = []
            for f_period, s_period in ema_pairs:
                e_fast = ema(close, f_period)
                e_slow = ema(close, s_period)
                
                # Cross detection
                bull_cross_now = (e_fast.iloc[-1] > e_slow.iloc[-1]) and (e_fast.iloc[-2] <= e_slow.iloc[-2])
                bear_cross_now = (e_fast.iloc[-1] < e_slow.iloc[-1]) and (e_fast.iloc[-2] >= e_slow.iloc[-2])

                # Distance and convergence
                gap_now = e_fast.iloc[-1] - e_slow.iloc[-1]
                gap_prev = e_fast.iloc[-2] - e_slow.iloc[-2]
                
                candles_away = None
                cross_type = "BULLISH" if gap_now < 0 else "BEARISH"
                
                if (gap_now > 0 and gap_now < gap_prev) or (gap_now < 0 and gap_now > gap_prev):
                    velocity = abs(gap_now - gap_prev)
                    if velocity > 0:
                        est = int(abs(gap_now) / velocity)
                        if est <= 20: candles_away = est

                ema_signals.append({
                    "label": f"{f_period}/{s_period} EMA",
                    "fast_val": round(e_fast.iloc[-1], 4),
                    "slow_val": round(e_slow.iloc[-1], 4),
                    "gap": round(gap_now, 4),
                    "bull_cross_now": bull_cross_now,
                    "bear_cross_now": bear_cross_now,
                    "candles_away": candles_away,
                    "pending_cross": cross_type
                })

            result.update({
                "ema_signals": ema_signals,
                "ema200": round(e200.iloc[-1], 4),
                "trend_200": "BULLISH" if price > e200.iloc[-1] else "BEARISH",
            })
            
            # Supertrend
            st_signals, st_lines = supertrend(df)
            result["supertrend"] = "BULLISH" if st_signals.iloc[-1] else "BEARISH"
            result["supertrend_val"] = round(st_lines.iloc[-1], 4)
            
            # VWAP
            vwap_series = vwap(df)
            vwap_last = vwap_series.iloc[-1]
            result["vwap"] = "BULLISH" if price > vwap_last else "BEARISH"
            result["vwap_val"] = round(vwap_last, 4)
            
        except Exception as e:
            logger.error(f"Error calculating EMAs for {symbol}: {str(e)}")
            result["error"] = f"EMA calculation error: {str(e)}"
            return result

        # ── Bollinger Bands ────────────────────────────────────────────────
        try:
            bbu, bbm, bbl = bollinger_bands(close)
            bb_upper, bb_mid, bb_lower = bbu.iloc[-1], bbm.iloc[-1], bbl.iloc[-1]
            bb_width = bb_upper - bb_lower
            pct_b = (price - bb_lower) / bb_width if bb_width != 0 else 0.5

            if price >= bb_upper * 0.999:   bb_pos = "TOUCHED_UPPER"
            elif price <= bb_lower * 1.001: bb_pos = "TOUCHED_LOWER"
            elif pct_b > 0.8:               bb_pos = "NEAR_UPPER"
            elif pct_b < 0.2:               bb_pos = "NEAR_LOWER"
            else:                           bb_pos = "MIDDLE"

            result.update({
                "bb_upper": round(bb_upper, 4), "bb_lower": round(bb_lower, 4),
                "bb_mid": round(bb_mid, 4), "bb_pos": bb_pos,
                "bb_pct_b": round(pct_b * 100, 1),
                "dist_upper_pct": round(((bb_upper - price) / price) * 100, 2),
                "dist_lower_pct": round(((price - bb_lower) / price) * 100, 2),
            })
        except Exception as e:
            logger.error(f"Error calculating BB for {symbol}: {str(e)}")

        # ── Volume ────────────────────────────────────────────────────────
        try:
            vol_recent = volume.iloc[-3:].mean()
            vol_prev = volume.iloc[-8:-3].mean()
            vol_ratio = vol_recent / vol_prev if vol_prev != 0 else 1.0
            result.update({
                "volume_trend": ("INCREASING" if vol_ratio > 1.05 else "DECREASING" if vol_ratio < 0.95 else "STABLE"),
                "volume_ratio": round(vol_ratio, 2),
                "volume_last":  round(volume.iloc[-1], 2),
            })
        except Exception as e:
            logger.error(f"Error calculating volume for {symbol}: {str(e)}")

        # ── RSI ───────────────────────────────────────────────────────────
        try:
            rsi_series = rsi(close)
            rsi_val = rsi_series.iloc[-1]
            result.update({
                "rsi": round(rsi_val, 1) if not np.isnan(rsi_val) else 50,
                "rsi_status": ("OVERBOUGHT" if rsi_val >= 70 else "OVERSOLD" if rsi_val <= 30 else "NEUTRAL"),
            })
        except Exception as e:
            logger.error(f"Error calculating RSI for {symbol}: {str(e)}")

        # ── Support / Resistance ──────────────────────────────────────────
        try:
            pivot_lb = 20
            swing_highs, swing_lows = pivot_levels(df, lookback=pivot_lb)
            
            res_levels = sorted([v for _, v in swing_highs if v > price * 0.995])
            sup_levels = sorted([v for _, v in swing_lows  if v < price * 1.005], reverse=True)
            nearest_res = res_levels[0] if res_levels else None
            nearest_sup = sup_levels[0] if sup_levels else None

            def c2l(lvl, pool):
                idxs = [i for i, v in pool if abs(v - lvl) / price < 0.005]
                return len(df) - 1 - max(idxs) if idxs else None

            res_candles = c2l(nearest_res, swing_highs) if nearest_res else None
            sup_candles = c2l(nearest_sup, swing_lows)  if nearest_sup else None

            # Detect recent breakouts (last 3-4 candles)
            old_res = [v for _, v in swing_highs if v < price and v > close.iloc[-4]]
            old_sup = [v for _, v in swing_lows if v > price and v < close.iloc[-4]]

            if old_res:
                sr_event = "BREAKOUT"
            elif old_sup:
                sr_event = "BREAKDOWN"
            elif nearest_sup and nearest_res:
                pos = (price - nearest_sup) / (nearest_res - nearest_sup)
                sr_event = ("CONSOLIDATING" if 0.35 < pos < 0.65 else "RETRACEMENT_FROM_TOP" if pos >= 0.65 else "RETRACEMENT_FROM_BOTTOM")
            else:
                sr_event = "UNDEFINED"

            result.update({
                "sr_event": sr_event,
                "nearest_res": round(nearest_res, 4) if nearest_res else None,
                "nearest_sup": round(nearest_sup, 4) if nearest_sup else None,
                "res_candles": res_candles,
                "sup_candles": sup_candles,
            })
        except Exception as e:
            logger.error(f"Error calculating S/R for {symbol}: {str(e)}")

        # ── Fibonacci ─────────────────────────────────────────────────────
        try:
            lb = min(100, len(df) - 1)
            sh, sl = high.iloc[-lb:].max(), low.iloc[-lb:].min()
            fib = fibonacci_levels(sh, sl)
            sorted_fibs = sorted(fib.items(), key=lambda x: x[1], reverse=True)
            current_fib = next((lbl for lbl, lvl in sorted_fibs if price >= lvl), sorted_fibs[-1][0])
            
            momentum = close.iloc[-1] - close.iloc[-5]
            if momentum > 0:
                next_fib = next(((l, round(v, 4)) for l, v in sorted(fib.items(), key=lambda x: x[1]) if v > price),
                                (sorted_fibs[0][0], round(sorted_fibs[0][1], 4)))
            else:
                next_fib = next(((l, round(v, 4)) for l, v in sorted(fib.items(), key=lambda x: x[1], reverse=True) if v < price),
                                (sorted_fibs[-1][0], round(sorted_fibs[-1][1], 4)))

            result.update({
                "fib_levels": {k: round(v, 4) for k, v in fib.items()},
                "fib_current_zone": current_fib, "fib_next_target": next_fib,
                "fib_swing_high": round(sh, 4), "fib_swing_low": round(sl, 4),
                "price": round(price, 4),
            })
        except Exception as e:
            logger.error(f"Error calculating Fibonacci for {symbol}: {str(e)}")
            result.update({
                "fib_levels": {}, "fib_current_zone": "ERROR",
                "fib_next_target": ("ERROR", 0), "fib_swing_high": 0,
                "fib_swing_low": 0, "price": round(price, 4),
            })

        # ── Patterns ──────────────────────────────────────────────────────
        bull_p, bear_p = detect_patterns(df)
        result["patterns_bull"] = bull_p
        result["patterns_bear"] = bear_p

        # 7. Bias Determination
        fib_pivot = result.get("fib_levels", {}).get("50%", 0)
        if fib_pivot > 0:
            dist_50 = abs(price - fib_pivot) / fib_pivot
            if dist_50 < 0.005:
                result["fib_bias"] = "NEUTRAL"
            elif price > fib_pivot:
                result["fib_bias"] = "BULLISH"
            else:
                result["fib_bias"] = "BEARISH"
        else:
            result["fib_bias"] = "NEUTRAL"

        # ── Strategy Engine (Final Recommendation) ────────────────────────
        score = 0
        
        # Trend (Supertrend & VWAP)
        if result["supertrend"] == "BULLISH": score += 2
        else: score -= 2
        
        if result["vwap"] == "BULLISH": score += 2
        else: score -= 2
        
        # Momentum (RSI & EMA)
        if rsi_val < 40: score += 1 # Potential reversal up
        elif rsi_val > 60: score -= 1 # Potential reversal down
        
        if any(e["pending_cross"] == "BULLISH" or e["bull_cross_now"] for e in ema_signals): score += 2
        if any(e["pending_cross"] == "BEARISH" or e["bear_cross_now"] for e in ema_signals): score -= 2
        
        # Price Action (S/R & BB)
        if sr_event == "BREAKOUT": score += 2
        elif sr_event == "BREAKDOWN": score -= 2
        
        if bb_pos == "TOUCHED_LOWER": score += 1
        elif bb_pos == "TOUCHED_UPPER": score -= 1
        
        # Patterns
        score += len(bull_p) * 2
        score -= len(bear_p) * 2
        
        # Final Signal
        final_signal = "WAIT"
        sl_pct = 0.0
        tp_pct = 0.0
        
        if score >= 5:
            final_signal = "BUY"
            # SL below Support or Lower BB
            sl_price = min(nearest_sup if nearest_sup else price*0.98, bb_lower) * 0.995
            tp_price = max(nearest_res if nearest_res else price*1.05, bb_upper) * 1.005
            sl_pct = abs(price - sl_price) / price * 100
            tp_pct = abs(price - tp_price) / price * 100
        elif score <= -5:
            final_signal = "SELL"
            # SL above Resistance or Upper BB
            sl_price = max(nearest_res if nearest_res else price*1.02, bb_upper) * 1.005
            tp_price = min(nearest_sup if nearest_sup else price*0.95, bb_lower) * 0.995
            sl_pct = abs(price - sl_price) / price * 100
            tp_pct = abs(price - tp_price) / price * 100

        result.update({
            "strategy_signal": final_signal,
            "strategy_score": score,
            "strategy_sl": round(sl_pct, 2),
            "strategy_tp": round(tp_pct, 2)
        })

        logger.info(f"✅ Successfully analysed {symbol} [{tf}] | Signal: {final_signal} (Score: {score})")
        return result

    except Exception as e:
        error_msg = f"Unexpected error in analysis for {symbol} [{tf}]: {str(e)}"
        logger.error(error_msg)
        result["error"] = error_msg
        return result

# ─── Render Helpers ──────────────────────────────────────────────────────────

def pill(text, kind="neu"):
    cls = {"bull": "pill-bull", "bear": "pill-bear", "neu": "pill-neu"}.get(kind, "pill-neu")
    return f'<span class="signal-pill {cls}">{text}</span>'

def color_val(text, kind):
    cls = {"bull":"bullish","bear":"bearish","neu":"neutral","accent":"accent","purple":"purple"}.get(kind,"")
    return f'<span class="{cls}">{text}</span>'

def render_metric(label, value_html):
    return f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value_html}</div></div>'

def render_tf_analysis(r: dict, is_india: bool = False):
    if r.get("error"):
        st.markdown(f'<div class="error-box">⚠ {r["error"]}</div>', unsafe_allow_html=True)
        return

    price = r["price"]
    cur   = r.get("currency", "₹")
    
    # ── Header: Smart Recommendation ──────────────────────────────────
    sk = {"BUY": "bull", "SELL": "bear", "WAIT": "neu"}.get(r["strategy_signal"], "neu")
    si = {"BUY": "🚀", "SELL": "📉", "WAIT": "⚖️"}.get(r["strategy_signal"], "⚖️")
    
    with st.container():
        sc1, sc2, sc3 = st.columns([2, 1, 1])
        with sc1:
            st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03); padding:15px; border-radius:10px; border-left:5px solid {('#00ff88' if sk=='bull' else '#ff4b4b' if sk=='bear' else '#6b7280')};">
                    <div style="color:#6b7280; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Smart Recommendation</div>
                    <div style="font-size:28px; font-weight:bold; margin:5px 0;">{si} {r['strategy_signal']}</div>
                    <div style="color:#6b7280; font-size:12px;">Strategy Score: <span style="color:{('#00ff88' if r['strategy_score']>0 else '#ff4b4b' if r['strategy_score']<0 else '#6b7280')}">{r['strategy_score']}</span></div>
                </div>
            """, unsafe_allow_html=True)
        
        if r["strategy_signal"] != "WAIT":
            with sc2:
                st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.03); padding:15px; border-radius:10px; text-align:center;">
                        <div style="color:#ff4b4b; font-size:12px; text-transform:uppercase;">Stop Loss (SL)</div>
                        <div style="font-size:20px; font-weight:bold;">{r['strategy_sl']}%</div>
                    </div>
                """, unsafe_allow_html=True)
            with sc3:
                st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.03); padding:15px; border-radius:10px; text-align:center;">
                        <div style="color:#00ff88; font-size:12px; text-transform:uppercase;">Take Profit (TP)</div>
                        <div style="font-size:20px; font-weight:bold;">{r['strategy_tp']}%</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            with sc2:
                st.info("Market is currently non-trending or showing mixed signals. Consolidation likely.")

    st.markdown('<hr style="border-color:rgba(255,255,255,0.05); margin:15px 0;">', unsafe_allow_html=True)

    cols  = st.columns(3)

    # ── Col 1: EMA / Trend / RSI ─────────────────────────────────────
    with cols[0]:
        st.markdown("**EMA SIGNALS**")

        for sig in r["ema_signals"]:
            label = sig["label"]
            if sig["bull_cross_now"]:
                cx = pill(f"🔥 {label} BULL CROSS NOW", "bull")
            elif sig["bear_cross_now"]:
                cx = pill(f"💀 {label} BEAR CROSS NOW", "bear")
            elif sig["candles_away"] is not None:
                k  = "bull" if sig["pending_cross"] == "BULLISH" else "bear"
                cx = pill(f"⏳ {label}: {sig['pending_cross']} CROSS ~{sig['candles_away']} CANDLES", k)
            else:
                gap = sig["gap"]
                k   = "bull" if gap > 0 else "bear"
                cx  = pill(f"{'▲' if gap>0 else '▼'} {label} | GAP {abs(gap):.2f}", k)
            st.markdown(render_metric(f"{label} CROSSOVER", cx), unsafe_allow_html=True)

        th  = pill("▲ BULLISH", "bull") if r["trend_200"] == "BULLISH" else pill("▼ BEARISH", "bear")
        th += f'<br><span style="font-size:10px;color:#6b7280">EMA200: {cur}{r["ema200"]:.2f}</span>'
        st.markdown(render_metric("200 EMA TREND", th), unsafe_allow_html=True)

        rk  = "bear" if r["rsi_status"]=="OVERBOUGHT" else "bull" if r["rsi_status"]=="OVERSOLD" else "neu"
        rh  = f'{color_val(str(r["rsi"]), rk)} {pill(r["rsi_status"], rk)}'
        st.markdown(render_metric("RSI (14)", rh), unsafe_allow_html=True)

        sk = "bull" if r["supertrend"] == "BULLISH" else "bear"
        sh = f'{pill(r["supertrend"], sk)}<br><span style="font-size:10px;color:#6b7280">Line: {cur}{r["supertrend_val"]:.2f}</span>'
        st.markdown(render_metric("SUPERTREND (10,3)", sh), unsafe_allow_html=True)

        vk = "bull" if r["vwap"] == "BULLISH" else "bear"
        vh = f'{pill(r["vwap"], vk)}<br><span style="font-size:10px;color:#6b7280">VWAP: {cur}{r["vwap_val"]:.2f}</span>'
        st.markdown(render_metric("VWAP (SESSION)", vh), unsafe_allow_html=True)

    # ── Col 2: Bollinger / Volume ─────────────────────────────────────
    with cols[1]:
        st.markdown("**BOLLINGER & VOLUME**")

        be = {"TOUCHED_UPPER":"🔴","TOUCHED_LOWER":"🟢","NEAR_UPPER":"🟠","NEAR_LOWER":"🟡","MIDDLE":"⚪"}.get(r["bb_pos"],"⚪")
        bk = {"TOUCHED_UPPER":"bear","NEAR_UPPER":"bear","TOUCHED_LOWER":"bull","NEAR_LOWER":"bull","MIDDLE":"neu"}.get(r["bb_pos"],"neu")
        bh  = f'{be} {pill(r["bb_pos"].replace("_"," "), bk)}<br>'
        bh += f'<span style="font-size:10px;color:#6b7280">U:{cur}{r["bb_upper"]:.2f} M:{cur}{r["bb_mid"]:.2f} L:{cur}{r["bb_lower"]:.2f}</span><br>'
        bh += f'<span style="font-size:10px;color:#6b7280">+{r["dist_upper_pct"]}% to Upper | -{r["dist_lower_pct"]}% to Lower | %B:{r["bb_pct_b"]}%</span>'
        st.markdown(render_metric("BOLLINGER BANDS", bh), unsafe_allow_html=True)

        vk = "bull" if r["volume_trend"]=="INCREASING" else "bear" if r["volume_trend"]=="DECREASING" else "neu"
        vi = "📈" if r["volume_trend"]=="INCREASING" else "📉" if r["volume_trend"]=="DECREASING" else "➡️"
        vh  = f'{vi} {pill(r["volume_trend"], vk)}<br>'
        vh += f'<span style="font-size:10px;color:#6b7280">Ratio(3/5 candles): {r["volume_ratio"]}x | Last: {r["volume_last"]:,.0f}</span>'
        st.markdown(render_metric("VOLUME ANALYSIS", vh), unsafe_allow_html=True)

    # ── Col 3: S/R / Fibonacci ────────────────────────────────────────
    with cols[2]:
        st.markdown("**S/R & FIBONACCI**")

        si = {"BREAKOUT":"🚀","BREAKDOWN":"💥","CONSOLIDATING":"⚖️",
              "RETRACEMENT_FROM_TOP":"🔄","RETRACEMENT_FROM_BOTTOM":"🔄","UNDEFINED":"❓"}
        sk = {"BREAKOUT":"bull","BREAKDOWN":"bear","CONSOLIDATING":"neu",
              "RETRACEMENT_FROM_TOP":"bear","RETRACEMENT_FROM_BOTTOM":"bull","UNDEFINED":"neu"}
        sh2  = f'{si.get(r["sr_event"],"❓")} {pill(r["sr_event"].replace("_"," "), sk.get(r["sr_event"],"neu"))}<br>'
        if r["nearest_res"]:
            dr = ((r["nearest_res"] - price) / price) * 100
            sh2 += f'<span style="font-size:10px;color:#ff6b8a">▲ RES: {cur}{r["nearest_res"]:.2f} (+{dr:.2f}%)'
            if r["res_candles"]: sh2 += f' | {r["res_candles"]} candles ago'
            sh2 += '</span><br>'
        if r["nearest_sup"]:
            ds = ((price - r["nearest_sup"]) / price) * 100
            sh2 += f'<span style="font-size:10px;color:#00ff88">▼ SUP: {cur}{r["nearest_sup"]:.2f} (-{ds:.2f}%)'
            if r["sup_candles"]: sh2 += f' | {r["sup_candles"]} candles ago'
            sh2 += '</span>'
        st.markdown(render_metric("S/R & PRICE ACTION", sh2), unsafe_allow_html=True)

        ntgt_lbl, ntgt_px = r["fib_next_target"]
        dist_to_tgt = abs(ntgt_px - price)
        dist_pct = (dist_to_tgt / price) * 100
        fd_icon   = "▲" if ntgt_px > price else "▼"
        fd_text   = "UPWARD TARGET" if ntgt_px > price else "DOWNWARD TARGET"
        
        fk = "bull" if r["fib_bias"] == "BULLISH" else "bear" if r["fib_bias"] == "BEARISH" else "neu"
        fh   = f'{pill(r["fib_bias"], fk)} | ZONE: <b>{color_val(r["fib_current_zone"], "accent")}</b><br>'
        fh  += f'🎯 {fd_text}: <b>{color_val(f"{ntgt_lbl} @ {cur}{ntgt_px}", "purple")}</b> {fd_icon}<br>'
        fh  += f'<span style="font-size:10px;color:#6b7280">Distance: {cur}{dist_to_tgt:.2f} ({dist_pct:.2f}%)</span><br>'
        fh  += f'<span style="font-size:10px;color:#6b7280">Range: {cur}{r["fib_swing_low"]} → {cur}{r["fib_swing_high"]}</span><br>'
        fh  += '<span style="font-size:10px;color:#6b7280; display:block; margin-top:4px; padding:4px; background:rgba(255,255,255,0.05); border-radius:4px;">'
        fh  += " | ".join([f"<b>{k}</b>:{cur}{v:.1f}" for k, v in r["fib_levels"].items()])
        fh  += '</span>'
        st.markdown(render_metric("FIBONACCI RETRACEMENT", fh), unsafe_allow_html=True)

    # ── Col 4: Patterns ───────────────────────────────────────────────
    st.markdown('<hr style="border-color:rgba(255,255,255,0.05); margin:8px 0;">', unsafe_allow_html=True)
    cols_p = st.columns(1)
    with cols_p[0]:
        ph = ""
        if r["patterns_bull"]:
            ph += f'<div style="margin-bottom:4px;">🟢 <b>Bullish:</b> ' + ", ".join([f'<span style="color:#00ff88">{p}</span>' for p in r["patterns_bull"]]) + '</div>'
        if r["patterns_bear"]:
            ph += f'<div style="margin-bottom:4px;">🔴 <b>Bearish:</b> ' + ", ".join([f'<span style="color:#ff6b8a">{p}</span>' for p in r["patterns_bear"]]) + '</div>'
        
        if not ph:
            ph = '<span style="color:#6b7280">No significant patterns detected in recent candles.</span>'
        
        st.markdown(render_metric("CHART & CANDLESTICK PATTERNS", ph), unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<h2 style="color:#00d4ff;font-family:Bebas Neue,sans-serif;letter-spacing:3px;">⚡ MTF SCALPER</h2>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#252830;">', unsafe_allow_html=True)

    # Market Selection
    market = st.selectbox("Market API", ["Delta Exchange (Crypto)", "Groww (India Stocks)", "CoinDCX Futures"], index=0)
    
    tickers_to_analyse = []
    
    if market == "Delta Exchange (Crypto)":
        default_tickers = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD"]
        ticker_input = st.text_input("Tickers (comma separated)", value=",".join(default_tickers))
        tickers_to_analyse = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
        is_india = False
        currency = "$"
    elif market == "CoinDCX Futures":
        gainers, last_update = get_coindcx_gainers()
        st.caption(f"⏱ Ticker list updated: {last_update} (30s cache)")
        if not gainers:
            st.warning("No tickers found with >10% gain in last 24h.")
            selected_gainers = []
        else:
            selected_labels = st.multiselect("Select Gainers", [g["label"] for g in gainers])
            selected_gainers = [g["sym"] for g in gainers if g["label"] in selected_labels]
        
        tickers_to_analyse = selected_gainers
        is_india = False
        currency = "$"
        
        st.markdown("---")
        st.subheader("🚀 Pump & Dump Scanner")
        col_p, col_d = st.columns(2)
        if col_p.button("🔥 PUMP", use_container_width=True):
            with st.spinner("Scanning for Pump candidates..."):
                st.session_state.scan_results = analyze_pump_dump_candidates(mode="PUMP")
            st.session_state.scan_mode = "PUMP"
        if col_d.button("📉 DUMP", use_container_width=True):
            with st.spinner("Scanning for Dump candidates..."):
                st.session_state.scan_results = analyze_pump_dump_candidates(mode="DUMP")
            st.session_state.scan_mode = "DUMP"
            
        if "scan_results" in st.session_state:
            mode = st.session_state.scan_mode
            st.markdown(f"**Potential {mode}s:**")
            if not st.session_state.scan_results:
                st.info("No strong candidates found.")
            else:
                for res in st.session_state.scan_results:
                    st.write(f"• **{res['Symbol']}**: {res['Prob']} ({res['Signal']})")
    else:
        # Groww
        st.markdown(
            '<div class="info-box">'
            '🔐 <b>Groww Trade API token required</b><br>'
            'Get one at <b>groww.in/trade-api</b> → API Keys.<br>'
            'Token expires every 24 h; refresh as needed.'
            '</div>',
            unsafe_allow_html=True,
        )
        groww_token = st.text_input(
            "GROWW BEARER TOKEN",
            type="password",
            placeholder="Paste Bearer token here…",
        )
        groww_exchange = st.selectbox(
            "EXCHANGE",
            options=["NSE", "BSE"],
            help="NSE for most equities/indices; BSE for BSE-listed stocks",
        )
        tickers_input = st.text_input(
            "SYMBOLS (comma separated)",
            value="RELIANCE,INFY,TCS",
            help="NSE/BSE trading symbols e.g. RELIANCE, INFY, NIFTY, HDFCBANK",
        )
        tickers_to_analyse = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        is_india = True
        currency = "₹"
        
        st.markdown("---")
        st.subheader("🚀 NSE Pump & Dump Scanner")
        
        index_choice = st.selectbox(
            "Scan Universe", 
            ["NIFTY 50", "NIFTY MIDCAP 150", "NIFTY SMALLCAP 250", "NIFTY 500"]
        )
        
        if index_choice == "NIFTY 50":
            scan_list = NIFTY_50
        elif index_choice == "NIFTY MIDCAP 150":
            scan_list = NIFTY_MIDCAP_150
        elif index_choice == "NIFTY SMALLCAP 250":
            scan_list = NIFTY_SMALLCAP_250
        else:
            scan_list = NIFTY_500
            
        col_p, col_d = st.columns(2)
        if col_p.button("🔥 PUMP", use_container_width=True, key="groww_pump"):
            with st.spinner(f"Scanning {index_choice} for Pump candidates..."):
                st.session_state.g_scan_results = analyze_groww_pump_dump_candidates(groww_token, groww_exchange, mode="PUMP", ticker_list=scan_list)
            st.session_state.g_scan_mode = "PUMP"
        if col_d.button("📉 DUMP", use_container_width=True, key="groww_dump"):
            with st.spinner(f"Scanning {index_choice} for Dump candidates..."):
                st.session_state.g_scan_results = analyze_groww_pump_dump_candidates(groww_token, groww_exchange, mode="DUMP", ticker_list=scan_list)
            st.session_state.g_scan_mode = "DUMP"
            
        if "g_scan_results" in st.session_state:
            mode = st.session_state.g_scan_mode
            st.markdown(f"**NSE Potential {mode}s:**")
            if not st.session_state.g_scan_results:
                st.info("No strong candidates found.")
            else:
                for res in st.session_state.g_scan_results:
                    st.write(f"• **{res['Symbol']}**: {res['Prob']} ({res['Signal']})")

    avail_tfs  = list(TF_CRYPTO.keys()) if not is_india else list(TF_INDIA.keys())
    timeframes = st.multiselect(
        "TIMEFRAMES",
        options=avail_tfs,
        default=["5m", "1h"],
    )
    
    ema_options = ["5/9", "9/21", "9/30", "20/50", "50/200"]
    selected_ema_pairs = st.multiselect(
        "EMA CROSSOVERS",
        options=ema_options,
        default=["9/21"],
    )

    st.markdown('<hr style="border-color:#252830;">', unsafe_allow_html=True)
    auto_refresh = st.checkbox("AUTO REFRESH (30 s)", value=False)
    run_btn      = st.button("🔍 RUN ANALYSIS")

# ─── Main Panel ──────────────────────────────────────────────────────────────
accent_col  = "#ff9500" if is_india else "#00d4ff"
mode_line   = ("🇮🇳 Indian Stocks · NSE/BSE · Groww"
               if is_india else "🪙 Crypto · Delta/CoinDCX")

st.markdown(
    f'<h1 style="font-family:Bebas Neue,sans-serif;letter-spacing:4px;color:{accent_col};margin-bottom:0;">'
    f'MULTI TIMEFRAME SCALPING DASHBOARD</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p style="color:#6b7280;font-size:12px;margin-top:2px;">'
    f'{mode_line} · Multiple EMA · Bollinger · RSI · Volume · S/R · Fibonacci</p>',
    unsafe_allow_html=True,
)

if auto_refresh:
    time.sleep(30)
    st.rerun()

if run_btn or auto_refresh:
    logger.info(f"Starting analysis run.")
    
    ema_pairs = [tuple(map(int, p.split("/"))) for p in selected_ema_pairs]

    if not tickers_to_analyse:
        st.error("Please enter/select at least one ticker.")
    elif not timeframes:
        st.error("Please select at least one timeframe.")
    else:
        for ticker in tickers_to_analyse:
            st.markdown(f'### {ticker}', unsafe_allow_html=True)

            for tf in timeframes:
                st.markdown(f'#### ⏱ {tf}', unsafe_allow_html=True)

                with st.spinner(f"Fetching {ticker} [{tf}]…"):
                    try:
                        if market == "Groww (India Stocks)":
                            df = fetch_groww_ohlcv(ticker, groww_exchange, tf, groww_token, limit=1000)
                        elif market == "CoinDCX Futures":
                            df = fetch_coindcx_ohlcv(ticker, tf, limit=1000)
                        else:
                            # Delta
                            df = fetch_delta_ohlcv(ticker, tf, limit=1000)

                        if df is None or df.empty:
                            st.warning(f"No data for {ticker} [{tf}]")
                            continue
                        
                        result = analyse(df, ticker, tf, ema_pairs=ema_pairs, currency=currency)
                        
                        if result.get("error"):
                            logger.warning(f"Analysis error for {ticker} [{tf}]: {result['error']}")
                        else:
                            logger.info(f"Analysis completed successfully for {ticker} [{tf}]")
                        
                        render_tf_analysis(result, is_india=is_india)

                    except requests.exceptions.Timeout as e:
                        error_msg = f"Request timeout for {ticker} [{tf}]. API took too long to respond."
                        logger.error(error_msg)
                        st.markdown(
                            f'<div class="error-box">⚠ TIMEOUT [{ticker} {tf}]: Request timed out. Try again later.</div>',
                            unsafe_allow_html=True,
                        )
                    
                    except requests.exceptions.ConnectionError as e:
                        error_msg = f"Connection error for {ticker} [{tf}]: {str(e)}"
                        logger.error(error_msg)
                        st.markdown(
                            f'<div class="error-box">⚠ CONNECTION ERROR [{ticker} {tf}]: Unable to reach API. Check your internet connection.</div>',
                            unsafe_allow_html=True,
                        )
                    
                    except requests.exceptions.HTTPError as e:
                        resp   = e.response
                        status = resp.status_code if resp is not None else "?"
                        error_msg = f"HTTP {status} error for {ticker} [{tf}]"
                        logger.error(f"{error_msg}: {e}")
                        
                        if status == 401:
                            hint = "🔐 Invalid or expired token — refresh at groww.in/trade-api."
                        elif status == 403:
                            hint = "🔒 Token lacks permission. Ensure Trade API subscription is active."
                        elif status == 404:
                            hint = "❌ Ticker not found. Check spelling or verify it exists on the chosen exchange."
                        elif status == 429:
                            hint = "⏱ Rate limited. Too many requests. Please wait and retry."
                        elif status == 500 or status == 502 or status == 503:
                            hint = "🔧 API server error. The service may be temporarily down."
                        else:
                            hint = (resp.text[:200] if resp is not None else str(e))
                        
                        st.markdown(
                            f'<div class="error-box">⚠ HTTP {status} [{ticker} {tf}]: {hint}</div>',
                            unsafe_allow_html=True,
                        )
                    
                    except ValueError as e:
                        error_msg = f"Data validation error for {ticker} [{tf}]: {str(e)}"
                        logger.error(error_msg)
                        
                        # Provide context-specific error messaging
                        error_str = str(e).lower()
                        
                        if "delta" in error_str and "unable to fetch" in error_str:
                            hint = (
                                f"⚠️ <b>Delta Exchange Data Unavailable</b><br>"
                                f"Even after trying multiple timeframes and time ranges, no data found for <b>{ticker}</b><br><br>"
                                f"<b>Possible reasons:</b><br>"
                                f"• This ticker may not be live-traded or may have limited historical data<br>"
                                f"• Delta Exchange might be experiencing temporary data issues<br>"
                                f"• Market data delay or update lag<br><br>"
                                f"<b>What to do:</b><br>"
                                f"1️⃣ <b>Switch to Groww</b> - Indian stocks with reliable data<br>"
                                f"2️⃣ Try a different crypto ticker: BTC<USD, ETHUSD<br>"
                                f"3️⃣ Wait a few minutes and try again<br>"
                                f"4️⃣ Check https://docs.delta.exchange for available instruments"
                            )
                        elif "unable to fetch" in error_str:
                            hint = str(e)
                        else:
                            hint = (
                                f"{str(e)}<br><br>"
                                f"<b>Quick fixes:</b><br>"
                                f"• Verify ticker format (uppercase): BTCUSD, ETHUSD, SOLUSD<br>"
                                f"• Try larger timeframe: Use 1h or 1d instead of 5m/15m<br>"
                                f"• Use Groww for Indian stocks (more stable data)"
                            )
                        
                        st.markdown(
                            f'<div class="error-box">⚠ DATA ERROR [{ticker} {tf}]:<br>{hint}</div>',
                            unsafe_allow_html=True,
                        )
                    
                    except Exception as e:
                        error_msg = f"Unexpected error for {ticker} [{tf}]: {type(e).__name__} - {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        st.markdown(
                            f'<div class="error-box">⚠ ERROR [{ticker} {tf}]: {type(e).__name__} - {str(e)[:100]}</div>',
                            unsafe_allow_html=True,
                        )

            st.markdown("---")

        logger.info("Analysis batch completed successfully")
        st.markdown(
            f'<p style="color:#6b7280;font-size:10px;">'
            f'Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
            unsafe_allow_html=True,
        )

else:
    st.markdown(f"""
    <div style="background:#111318;border:1px dashed #252830;border-radius:8px;
                padding:48px;text-align:center;margin-top:40px;">
        <div style="font-family:Bebas Neue,sans-serif;font-size:36px;
                    color:#252830;letter-spacing:4px;">AWAITING ANALYSIS</div>
        <div style="color:#6b7280;font-size:12px;margin-top:8px;">
            Select market → Enter tickers → Choose timeframes → Click RUN ANALYSIS
        </div>
        <div style="margin-top:24px;display:flex;justify-content:center;gap:20px;flex-wrap:wrap;">
            <span class="source-badge badge-crypto" style="font-size:13px;padding:8px 22px;">
                🪙 CRYPTO — Delta Exchange
            </span>
            <span class="source-badge badge-india"  style="font-size:13px;padding:8px 22px;">
                🇮🇳 INDIAN STOCKS — Groww
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
