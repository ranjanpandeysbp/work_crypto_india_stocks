# Sample Log Messages & Error Scenarios

## Successful Run Log Example

```
2026-04-26 14:30:22,145 - __main__ - INFO - Starting analysis run. Market: Delta, Mode: manual
2026-04-26 14:30:22,156 - __main__ - INFO - Validation passed. Tickers: ['BTCUSD', 'ETHUSD'], Timeframes: ['5m', '1h']
2026-04-26 14:30:22,200 - __main__ - INFO - Processing BTCUSD [5m] on Delta
2026-04-26 14:30:22,220 - __main__ - INFO - Fetching Delta Exchange data: symbol=BTCUSD, resolution=5m, limit=300
2026-04-26 14:30:23,450 - __main__ - INFO - ✅ Successfully fetched 300 candles for BTCUSD [5m]
2026-04-26 14:30:23,455 - __main__ - INFO - Starting analysis for BTCUSD [5m] with 300 candles
2026-04-26 14:30:23,475 - __main__ - DEBUG - EMA Calculated: 9=46253.5432, 21=45821.2301, 200=44925.1234
2026-04-26 14:30:23,485 - __main__ - INFO - ✅ Successfully analysed BTCUSD [5m]
2026-04-26 14:30:23,490 - __main__ - INFO - Processing ETHUSD [5m] on Delta
2026-04-26 14:30:23,510 - __main__ - INFO - Fetching Delta Exchange data: symbol=ETHUSD, resolution=5m, limit=300
2026-04-26 14:30:24,120 - __main__ - INFO - ✅ Successfully fetched 300 candles for ETHUSD [5m]
2026-04-26 14:30:24,125 - __main__ - INFO - Starting analysis for ETHUSD [5m] with 300 candles
2026-04-26 14:30:24,150 - __main__ - INFO - ✅ Successfully analysed ETHUSD [5m]
2026-04-26 14:30:24,155 - __main__ - INFO - Analysis batch completed successfully
```

---

## Error Scenarios & Corresponding Logs

### Scenario 1: Ticker Not Found

```
2026-04-26 14:35:10,200 - __main__ - INFO - Processing FAKECOIN [1h] on Delta
2026-04-26 14:35:10,210 - __main__ - INFO - Fetching Delta Exchange data: symbol=FAKECOIN, resolution=1h, limit=300
2026-04-26 14:35:11,300 - __main__ - ERROR - Ticker 'FAKECOIN' not found or no data available on Delta Exchange
```

**User sees:**
```
⚠ DATA ERROR [FAKECOIN 1h]: Ticker 'FAKECOIN' not found or no data available on Delta Exchange
```

---

### Scenario 2: Groww Token Missing or Expired

```
2026-04-26 14:40:15,100 - __main__ - INFO - Starting analysis run. Market: Groww, Mode: manual
2026-04-26 14:40:15,110 - __main__ - ERROR - Groww token is missing or empty
```

**User sees:**
```
⚠ Please enter your Groww Bearer token in the sidebar.
Obtain it from groww.in/trade-api → API Keys.
Note: Tokens expire every 24 hours and need to be refreshed.
```

---

### Scenario 3: Groww Authentication Failed

```
2026-04-26 14:45:20,150 - __main__ - INFO - Processing RELIANCE [1h] on Groww
2026-04-26 14:45:20,160 - __main__ - INFO - Fetching Groww data: symbol=RELIANCE, exchange=NSE, tf=1h, limit=300
2026-04-26 14:45:20,170 - __main__ - INFO - Attempt 1: Trying new backtesting endpoint with symbol NSE-RELIANCE
2026-04-26 14:45:21,200 - __main__ - ERROR - Groww authentication failed (401). Token may be invalid or expired
```

**User sees:**
```
⚠ HTTP 401 [RELIANCE 1h]: 🔐 Invalid or expired token — refresh at groww.in/trade-api.
```

---

### Scenario 4: Permission Denied (API Subscription Issue)

```
2026-04-26 14:50:22,100 - __main__ - INFO - Processing INFY [5m] on Groww
2026-04-26 14:50:22,110 - __main__ - INFO - Fetching Groww data: symbol=INFY, exchange=NSE, tf=5m, limit=300
2026-04-26 14:50:22,120 - __main__ - INFO - Attempt 1: Trying new backtesting endpoint with symbol NSE-INFY
2026-04-26 14:50:23,150 - __main__ - ERROR - Groww permission denied (403). Trade API subscription may be inactive
```

**User sees:**
```
⚠ HTTP 403 [INFY 5m]: 🔒 Token lacks permission. Ensure Trade API subscription is active.
```

---

### Scenario 5: Symbol Not Found on Exchange

```
2026-04-26 14:55:25,100 - __main__ - INFO - Processing FAKESTOCK [1d] on Groww
2026-04-26 14:55:25,110 - __main__ - INFO - Fetching Groww data: symbol=FAKESTOCK, exchange=NSE, tf=1d, limit=300
2026-04-26 14:55:25,120 - __main__ - INFO - Attempt 1: Trying new backtesting endpoint with symbol NSE-FAKESTOCK
2026-04-26 14:55:26,150 - __main__ - WARNING - Symbol NSE-FAKESTOCK not found on new endpoint (404), trying legacy endpoint
2026-04-26 14:55:26,160 - __main__ - INFO - Attempt 2: Trying legacy candle/range endpoint for FAKESTOCK
2026-04-26 14:55:27,200 - __main__ - ERROR - Symbol 'FAKESTOCK' not found on NSE. Check spelling and exchange selection
```

**User sees:**
```
⚠ HTTP 404 [FAKESTOCK 1d]: ❌ Ticker not found. Check spelling or verify it exists on the chosen exchange.
```

---

### Scenario 6: Request Timeout

```
2026-04-26 15:00:30,100 - __main__ - INFO - Processing BTCUSD [15m] on Delta
2026-04-26 15:00:30,110 - __main__ - INFO - Fetching Delta Exchange data: symbol=BTCUSD, resolution=15m, limit=300
2026-04-26 15:00:45,500 - __main__ - ERROR - Request timeout while fetching BTCUSD from Delta Exchange: Request timed out
```

**User sees:**
```
⚠ TIMEOUT [BTCUSD 15m]: Request timed out. API took too long to respond. Try again later.
```

---

### Scenario 7: Connection Error (Internet Issue)

```
2026-04-26 15:05:32,100 - __main__ - INFO - Processing ETHUSD [1h] on Delta
2026-04-26 15:05:32,110 - __main__ - INFO - Fetching Delta Exchange data: symbol=ETHUSD, resolution=1h, limit=300
2026-04-26 15:05:33,200 - __main__ - ERROR - Connection error to Delta Exchange: HTTPConnectionPool(host='api.delta.exchange', port=443): Max retries exceeded
```

**User sees:**
```
⚠ CONNECTION ERROR [ETHUSD 1h]: Unable to reach API. Check your internet connection.
```

---

### Scenario 8: Insufficient Data (Less than 210 candles)

```
2026-04-26 15:10:35,100 - __main__ - INFO - Processing TINY [1m] on Delta
2026-04-26 15:10:35,110 - __main__ - INFO - Fetching Delta Exchange data: symbol=TINY, resolution=1m, limit=300
2026-04-26 15:10:35,450 - __main__ - INFO - ✅ Successfully fetched 50 candles for TINY [1m]
2026-04-26 15:10:35,455 - __main__ - INFO - Starting analysis for TINY [1m] with 50 candles
2026-04-26 15:10:35,460 - __main__ - WARNING - Only 50 candles fetched (need ≥210). Try a longer-history timeframe or a symbol with more data.
```

**User sees:**
```
⚠ Only 50 candles fetched (need ≥210). Try a longer-history timeframe or a symbol with more data.
```

---

### Scenario 9: Invalid Data/NaN Values

```
2026-04-26 15:15:40,100 - __main__ - INFO - Processing STOCK [1h] on Groww
2026-04-26 15:15:40,110 - __main__ - INFO - Fetching Groww data: symbol=STOCK, exchange=NSE, tf=1h, limit=300
2026-04-26 15:15:41,300 - __main__ - INFO - ✅ Successfully fetched 300 candles via legacy endpoint
2026-04-26 15:15:41,310 - __main__ - INFO - Starting analysis for STOCK [1h] with 300 candles
2026-04-26 15:15:41,320 - __main__ - WARNING - RSI calculated as NaN for STOCK, using 50
2026-04-26 15:15:41,330 - __main__ - WARNING - Previous volume is 0 for STOCK
2026-04-26 15:15:41,340 - __main__ - INFO - ✅ Successfully analysed STOCK [1h]
```

---

### Scenario 10: Rate Limiting

```
2026-04-26 15:20:45,100 - __main__ - INFO - Processing RELIANCE [5m] on Groww
2026-04-26 15:20:45,110 - __main__ - INFO - Fetching Groww data: symbol=RELIANCE, exchange=NSE, tf=5m, limit=300
2026-04-26 15:20:46,200 - __main__ - ERROR - Groww API HTTP 429: {"message": "Rate limit exceeded. Max 10 requests per minute."}
```

**User sees:**
```
⚠ HTTP 429 [RELIANCE 5m]: ⏱ Rate limited. Too many requests. Please wait and retry.
```

---

## Key Features Demonstrated

✅ **Hierarchical logging** - Each step tracked from start to finish
✅ **Context preservation** - Ticker, timeframe, market always included
✅ **Error classification** - Different handlers for different error types
✅ **User-friendly messages** - Technical logs + human UI messages
✅ **Graceful fallbacks** - Attempt new endpoint → fallback to legacy
✅ **Data validation** - NaN handling, volume checks, price sanity checks
✅ **Actionable guidance** - Each error includes what user should do next

