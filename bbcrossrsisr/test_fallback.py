#!/usr/bin/env python3
"""Test the new fallback strategy in fetch_delta_ohlcv()"""

import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

print("=" * 70)
print("Testing Delta Exchange Fallback Strategy")
print("=" * 70)

try:
    # Import after path is set
    from scalping_strategy import fetch_delta_ohlcv
    
    print("\nTest 1: BTCUSD with 15m timeframe")
    print("-" * 70)
    
    try:
        df = fetch_delta_ohlcv("BTCUSD", "15m", limit=50)
        print(f"✅ SUCCESS! Got {len(df)} candles")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   First timestamp: {df['time'].iloc[0]}")
            print(f"   Last timestamp: {df['time'].iloc[-1]}")
    except ValueError as e:
        error_str = str(e)
        if "Unable to fetch" in error_str:
            print(f"⚠️  Could not fetch - strategies exhausted")
            print(f"   Message: {error_str[:100]}...")
        else:
            print(f"❌ Error: {error_str[:100]}...")
    except Exception as e:
        print(f"❌ {type(e).__name__}: {str(e)[:100]}")
    
    print("\n" + "=" * 70)
    print("Test 2: ETHUSD with 1h timeframe")
    print("-" * 70)
    
    try:
        df = fetch_delta_ohlcv("ETHUSD", "1h", limit=50)
        print(f"✅ SUCCESS! Got {len(df)} candles")
    except ValueError as e:
        print(f"⚠️  No data: {str(e)[:150]}...")
    except Exception as e:
        print(f"❌ {type(e).__name__}: {str(e)[:100]}")
    
    print("\n" + "=" * 70)
    print("If 'Unable to fetch' message appears, it means:")
    print("  - Fallback strategies (older data, larger timeframes) all returned empty")
    print("  - Delta Exchange has no accessible data for these tickers")
    print("  - This is expected and the UI will show helpful suggestions")
    print("=" * 70)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure you're in the bbcrossrsisr directory")
    sys.exit(1)
