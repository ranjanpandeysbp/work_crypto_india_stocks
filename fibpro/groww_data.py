import os
import pandas as pd
from dotenv import load_dotenv
import sys
from datetime import datetime, timedelta
from growwapi import GrowwAPI

load_dotenv()

API_TOKEN = os.getenv("GROWW_ACCESS_TOKEN")

# Initialize Groww API client
try:
    groww = GrowwAPI(API_TOKEN)
except Exception as e:
    print(f"ERROR: Failed to initialize Groww API: {e}", file=sys.stderr)
    groww = None

def fetch_ohlc(symbol, interval="day", days=100):
    """Fetch OHLC data from Groww API using the official SDK"""
    
    if groww is None:
        print(f"ERROR: {symbol} - Groww API not initialized", file=sys.stderr)
        return None

    try:
        if not API_TOKEN:
            print(f"ERROR: GROWW_ACCESS_TOKEN not configured in .env file", file=sys.stderr)
            return None

        # Convert interval to minutes (API requires interval in minutes)
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "10m": 10,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "day": 1440,
            "1w": 10080,
            "weekly": 10080
        }.get(interval, 1440)

        # API data availability limits per interval
        max_days_map = {
            1: 7,      # 1m: 7 days
            5: 15,     # 5m: 15 days
            10: 30,    # 10m: 30 days
            15: 60,    # 15m: ~60 days (estimate)
            30: 90,    # 30m: ~90 days (estimate)
            60: 150,   # 1h: 150 days
            240: 365,  # 4h: 365 days
            1440: 1080, # 1d: 1080 days (~3 years)
            10080: 3650 # 1w: No limit (set to ~10 years)
        }
        
        # Adjust days to stay within API limits
        max_days = max_days_map.get(interval_minutes, 1080)
        adjusted_days = min(days, max_days)
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=adjusted_days)

        # Fetch historical data
        response = groww.get_historical_candle_data(
            trading_symbol=symbol,
            exchange=groww.EXCHANGE_NSE,
            segment=groww.SEGMENT_CASH,
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            interval_in_minutes=interval_minutes
        )

        if not response or "candles" not in response or not response["candles"]:
            print(f"WARNING: {symbol} - No candle data returned from API", file=sys.stderr)
            return None

        # Convert response to DataFrame
        candles = response["candles"]
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        # Convert timestamp to datetime
        df["Date"] = pd.to_datetime(df["timestamp"], unit="s")
        df = df[["Date", "open", "high", "low", "close", "volume"]]
        df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        
        print(f"✓ {symbol} [{interval}]: Fetched {len(df)} candles ({adjusted_days}d)", file=sys.stderr)
        return df

    except Exception as e:
        print(f"ERROR: {symbol} - {type(e).__name__}: {str(e)}", file=sys.stderr)
        return None