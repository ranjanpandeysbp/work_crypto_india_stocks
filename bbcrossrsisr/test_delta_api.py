#!/usr/bin/env python3
"""
Quick test script to verify Delta Exchange API connectivity and response format.
Run this to debug "no data available" errors.
"""

import requests
import json
from datetime import datetime, timezone

DELTA_BASE = "https://api.delta.exchange"

def test_delta_api(symbol="BTCUSD", resolution="1h", limit=10):
    """Test Delta Exchange API and show raw response."""
    
    print(f"\n{'='*70}")
    print(f"Testing Delta Exchange API")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Resolution: {resolution}")
    print(f"Limit: {limit} candles")
    print(f"Endpoint: {DELTA_BASE}/v2/history/candles")
    
    # Calculate time range
    secs = {
        "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
        "1h": 3600, "4h": 14400, "1d": 86400
    }.get(resolution, 3600)
    
    end_ts = int(datetime.now(timezone.utc).timestamp())
    start_ts = end_ts - secs * limit
    
    print(f"Time range: {start_ts} → {end_ts}")
    print(f"  From: {datetime.fromtimestamp(start_ts)}")
    print(f"  To:   {datetime.fromtimestamp(end_ts)}")
    
    params = {
        "resolution": resolution,
        "symbol": symbol.upper(),
        "start": start_ts,
        "end": end_ts
    }
    
    print(f"\nRequest params: {params}")
    
    try:
        print(f"\n{'─'*70}")
        print("Making request...")
        print(f"{'─'*70}")
        
        r = requests.get(
            f"{DELTA_BASE}/v2/history/candles",
            params=params,
            timeout=10,
        )
        
        print(f"Status Code: {r.status_code}")
        print(f"Headers: {dict(r.headers)}")
        
        data = r.json()
        
        print(f"\n{'─'*70}")
        print("RESPONSE:")
        print(f"{'─'*70}")
        print(json.dumps(data, indent=2))
        
        print(f"\n{'─'*70}")
        print("ANALYSIS:")
        print(f"{'─'*70}")
        
        success = data.get("success")
        result = data.get("result", [])
        message = data.get("message", "N/A")
        
        print(f"✓ success: {success}")
        print(f"✓ message: {message}")
        print(f"✓ result type: {type(result)}")
        print(f"✓ result length: {len(result) if isinstance(result, list) else 'N/A'}")
        
        if isinstance(result, list) and len(result) > 0:
            print(f"\nFirst candle: {result[0]}")
            print(f"Candle structure: time, open, high, low, close, volume")
        
        if success and result:
            print(f"\n✅ SUCCESS: Got {len(result)} candles!")
            return True
        else:
            print(f"\n❌ FAILURE: No data returned or success=false")
            return False
            
    except requests.exceptions.Timeout as e:
        print(f"\n❌ TIMEOUT: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        print("   → Check internet connection")
        print("   → Verify api.delta.exchange is accessible")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        return False


def test_multiple_tickers():
    """Test multiple common tickers."""
    tickers = ["BTCUSD", "ETHUSD", "SOLUSD"]
    resolution = "1h"
    
    print(f"\n\n{'='*70}")
    print("Testing multiple tickers with 1h timeframe")
    print(f"{'='*70}\n")
    
    results = {}
    for ticker in tickers:
        success = test_delta_api(ticker, resolution)
        results[ticker] = "✅ OK" if success else "❌ FAILED"
    
    print(f"\n\n{'='*70}")
    print("SUMMARY:")
    print(f"{'='*70}")
    for ticker, status in results.items():
        print(f"{ticker:15} {status}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test single ticker
        symbol = sys.argv[1]
        resolution = sys.argv[2] if len(sys.argv) > 2 else "1h"
        test_delta_api(symbol, resolution)
    else:
        # Test multiple tickers
        test_multiple_tickers()
    
    print(f"\n{'='*70}")
    print("If errors persist:")
    print(f"  1. Check internet connection")
    print(f"  2. Verify ticker format (uppercase, e.g., BTCUSD)")
    print(f"  3. Try different timeframe (1h, 4h, 1d)")
    print(f"  4. Check Delta Exchange status: https://delta.exchange")
    print(f"{'='*70}\n")
