# Delta Exchange Ticker Troubleshooting Guide

## Issue: "Ticker not found or no data available on Delta Exchange"

This error occurs when `scalping_strategy.py` cannot fetch data for a ticker from the Delta Exchange API.

---

## Causes & Solutions

### 1. **Incorrect Ticker Format**
**Problem:** Ticker name doesn't match Delta Exchange conventions

**Solution:**
- ✅ **Correct format:** `BTCUSD`, `ETHUSD`, `SOLUSD` (uppercase, ends with USD)
- ❌ **Wrong formats:** `BTC`, `ETH-USD`, `Bitcoin`, `btcusd` (lowercase)

**Common Valid Tickers:**
- `BTCUSD` - Bitcoin
- `ETHUSD` - Ethereum  
- `SOLUSD` - Solana
- `LTCUSD` - Litecoin
- `DOGEUSD` - Dogecoin
- `BNBUSD` - Binance Coin
- `XRPUSD` - Ripple
- `ADAUSD` - Cardano
- `AVAXUSD` - Avalanche
- `UNIUSD` - Uniswap
- `LINKUSD` - Chainlink

---

### 2. **Invalid Timeframe for this Ticker**
**Problem:** The ticker exists, but no data is available for the selected timeframe

**Solution:**
- Try a **larger timeframe** (1h, 4h, 1d instead of 1m, 5m)
- Newer pairs may only have data for daily charts
- Try 1d first to verify the ticker exists

**Recommended timeframes by data availability:**
- `1d` → Most complete data (all tickers)
- `4h`, `1h` → Usually available
- `15m`, `5m` → May be limited for newer pairs
- `1m`, `3m` → Least available data

---

### 3. **API Endpoint Changed or Updated**
**Problem:** Delta Exchange API structure may have changed

**Debug Steps:**
1. Check `scalping_strategy.log` for the exact error
2. Look for the raw API response in logs
3. Visit https://api.delta.exchange/v2/history/candles directly in browser

**Test URL Format:**
```
https://api.delta.exchange/v2/history/candles?symbol=BTCUSD&resolution=1h&start=1700000000&end=1800000000
```

---

### 4. **Market Closed or No Recent Data**
**Problem:** The crypto market is open 24/7, but historical data may be sparse

**Solution:**
- Crypto markets trade 24/7, so this usually isn't an issue
- If using very recent pairs, older timeframes may have no data
- Try with major pairs like BTCUSD, ETHUSD first

---

### 5. **API Rate Limiting or Temporary Outage**
**Problem:** Delta Exchange API may be rate-limiting or temporarily unavailable

**Symptoms:**
- "Unexpected error" or timeout messages
- Multiple tickers failing simultaneously
- Errors appear intermittently

**Solution:**
- Wait a few minutes
- Check https://delta.exchange status
- Reduce number of tickers/timeframes


---

## Debugging Steps

### Step 1: Verify Ticker Format
```
❌ Wrong: BTC, Bitcoin, btc, BTC-USD
✅ Right: BTCUSD (all uppercase)
```

### Step 2: Check Log File
Look at `scalping_strategy.log` in the app directory:
```
ERROR - Ticker 'BTCUSD' not found or no data available on Delta Exchange
```

### Step 3: Try Single Ticker + Large Timeframe
1. Change tickers to just: `BTCUSD`
2. Change timeframes to just: `1d`
3. Click RUN → See if it works

### Step 4: Test API Directly
Open this in your browser (replace values):
```
https://api.delta.exchange/v2/history/candles?symbol=BTCUSD&resolution=1h&start=1700000000&end=1800000000
```

If you see JSON data with `"success": true` and `"result": [...]` → API works
If you see `"success": false` → API is returning error
If page won't load → Check internet/Delta is down

---

## Error Messages & Meanings

| Error | Cause | Solution |
|-------|-------|----------|
| "Ticker 'XXXX' not found or no data available" | Invalid ticker or no data | Verify ticker format above |
| "Request timed out" | API too slow | Wait and retry later |
| "Could not connect to api.delta.exchange" | No internet or API down | Check internet/Delta status |
| "HTTP 429" | Rate limited | Wait before retrying |
| "HTTP 500" | Server error | Delta having issues, try later |

---

## Solutions by Scenario

### Scenario A: BTCUSD works, but other tickers fail
- → Ticker names may be wrong (check capitalization)
- → Some tickers may not exist on Delta

### Scenario B: All tickers fail with same error
- → Check internet connection
- → Try in 1-2 minutes (potential outage)
- → Verify ticker format (uppercase + USD suffix)

### Scenario C: Works with 1d, fails with 5m
- → Ticker exists but 5m data unavailable
- → Try 1h, 4h, 1d timeframes instead

### Scenario D: Specific timeframe fails for all tickers
- → May be a timeframe issue
- → Try `5m`, `1h`, `4h`, `1d` instead

---

## Recommended Starting Test

**Step 1:** Use defaults in app (BTCUSD, ETHUSD)
**Step 2:** Select timeframes: 1h, 4h, 1d (skip fast 5m, 15m)
**Step 3:** Click RUN ANALYSIS
**Step 4:** If this works → issue is with your custom settings

---

## Log File Location

**File:** `f:\ranjan\work\strategy\bbcrossrsisr\scalping_strategy.log`

**To view recent errors:**
```powershell
# Show last 50 lines of log
Get-Content scalping_strategy.log -Tail 50

# Search for errors
Select-String "ERROR" scalping_strategy.log
```

---

## Contact / Documentation

- **Delta Exchange API Docs:** https://docs.delta.exchange/
- **Supported Symbols:** Check Delta Exchange website symbol list
- **Historical Data:** Limited by timeframe; newer pairs have less history
