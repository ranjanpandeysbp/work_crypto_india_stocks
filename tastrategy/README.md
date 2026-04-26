# 📊 AI Swing Trading Dashboard — NSE/BSE
### Multi-Strategy Scanner with AI Scoring & Telegram Alerts

---

## 🚀 Quick Start

```bash
pip install streamlit pandas plotly groq python-dotenv requests growwapi

# Configure .env (see Environment Setup below)

streamlit run app.py
```

---

## 📁 Project Structure

```
├── app.py           — Streamlit dashboard (UI + orchestration)
├── strategy.py      — All 9 trading strategies + indicator library
├── ai_filter.py     — Groq LLM scoring layer
├── alerts.py        — Telegram alert sender
├── groww_data.py    — Groww API data fetcher
├── logger.py        — Trade history (CSV)
├── .env             — API keys (never commit this)
└── README.md        — This file
```

---

## ⚙️ Environment Setup

Create a `.env` file in the project root:

```env
GROWW_ACCESS_TOKEN=your_groww_api_token_here
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Getting API Keys:**
- **Groww**: Apply at [Groww Developer Portal](https://groww.in/open-api)
- **Groq**: Free key at [console.groq.com](https://console.groq.com)
- **Telegram Bot**: Create via [@BotFather](https://t.me/BotFather) on Telegram

---

## 🎯 How to Use

1. Open the app — select a **strategy** from the sidebar dropdown
2. Enter your **symbols** (e.g., `RELIANCE,INFY,TCS,HDFCBANK`)
3. Choose the **lower timeframe** (1h recommended for swing trading)
4. Click **🔍 Scan Market**
5. Review results, signals, AI scores, and chart

The app fetches:
- **HTF (Higher Timeframe)**: Daily candles — for trend context
- **LTF (Lower Timeframe)**: Your selected timeframe — for entry signals

---

## 📈 Strategy Guide

---

### 1. 🔁 RSI + MACD Combo

**Type:** Momentum Confirmation | **Hold:** 5–15 days

**How it works:**
Uses two momentum indicators in combination — RSI identifies oversold conditions, MACD confirms the direction of momentum. Both must agree for a high-probability entry.

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| Price above EMA50 (HTF) | +15 | Uptrend confirmed |
| EMA50 > EMA200 (HTF) | +10 | Bull market structure |
| RSI 30–45 | +25 | Oversold bounce opportunity |
| MACD fresh bullish crossover | +25 | Momentum confirmed |
| Volume ≥ 1.5x | +15 | Institutional participation |

**Entry Rules:**
- RSI between 30–45 on LTF
- MACD line crosses above signal line
- Price must be above EMA50 on daily chart

**Exit Rules:**
- 🎯 Target: RSI reaches 65–70
- 🛑 SL: 1.5 × ATR below entry
- Min R:R = 1:2

**Best For:** RELIANCE, INFY, TCS, HDFCBANK

---

### 2. 📈 EMA Crossover (Trend Following)

**Type:** Trend Following | **Hold:** 10–30 days

**How it works:**
Identifies when a fast EMA crosses above a slow EMA, signaling a trend shift. The "perfect stack" (Price > EMA9 > EMA20 > EMA50) is the strongest confirmation.

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| HTF price above EMA50 | +20 | Major trend aligned |
| EMA50 > EMA200 (HTF) | +10 | Golden cross structure |
| Fresh EMA20 × EMA50 cross | +35 | Prime entry trigger |
| Perfect EMA stack | +20 | Maximum trend alignment |
| EMA20 slope > 0.3% | +15 | Strong momentum |

**Entry Rules:**
- EMA20 crosses above EMA50 on LTF (fresh cross = highest score)
- Ideally: Price > EMA9 > EMA20 > EMA50 (perfect stack)
- HTF daily chart must show price above EMA50

**Exit Rules:**
- 🎯 Target: 2.5 × ATR above entry
- 🛑 SL: Below EMA50 on LTF (−0.5 ATR buffer)
- Trail: Move SL to EMA20 as trade progresses
- Emergency exit: EMA20 crosses back below EMA50

**Best For:** TATAMOTORS, AXISBANK, SBIN, BAJFINANCE

---

### 3. 🧱 Support & Resistance Breakout

**Type:** Breakout | **Hold:** 7–20 days

**How it works:**
Identifies when price breaks above a key resistance level (20-period swing high) with strong volume. The volume confirmation is MANDATORY — without it, most breakouts fail.

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| Fresh resistance breakout | +40 | Core signal |
| Volume ≥ 2.0x | +25 | Institutional breakout |
| Volume 1.5–2.0x | +18 | Confirmed breakout |
| Tight consolidation (<3%) | +15 | Clean base formed |
| RSI 50–70 | +10 | Momentum supporting |

**Entry Rules:**
- Price closes ABOVE the 20-period swing high
- Volume must be ≥ 1.5x average (non-negotiable)
- Price should be within 3% of the breakout level (don't chase)
- Consolidation of 3–5+ candles before breakout (forms a base)

**Exit Rules:**
- 🎯 Target: Next major resistance / 3 × ATR
- 🛑 SL: Below breakout candle's low (−0.3 ATR)
- ❌ If price closes back below breakout level: EXIT immediately
- 🔁 Re-test as support = opportunity to add position

**Best For:** F&O stocks, BANKBARODA, ONGC, NTPC

---

### 4. 🎯 Fibonacci Retracement (Upgraded)

**Type:** Pullback Entry | **Hold:** 7–15 days

**How it works:**
In an established uptrend, price often pulls back to key Fibonacci levels before resuming upward. The 61.8% ("Golden Ratio") level is the most powerful entry zone. Volume should DECREASE during pullback (healthy retracement) and volume should return as price bounces.

**Fibonacci Levels:**
| Level | Score | Reliability |
|-------|-------|-------------|
| 38.2% Retracement | +30 | Good (shallow pullback) |
| 50.0% Retracement | +35 | Very Good |
| 61.8% Golden Ratio | +40 | BEST — highest probability |
| 78.6% Retracement | +20 | Risky (deep pullback) |

**Entry Rules:**
- HTF must show clear uptrend (price above EMA50)
- Price must pull back to 38.2%, 50%, or 61.8% Fibonacci level
- Volume should be declining during pullback
- RSI should be recovering (35–55) and turning upward
- Look for a confirmation candle (hammer, bullish engulfing) at the Fib level

**Exit Rules:**
- 🎯 Target: Previous swing high (100% Fibonacci)
- 🎯 Extended target: 127.2% Fibonacci extension
- 🛑 SL: Below 78.6% Fib level (−0.5 ATR buffer)
- ❌ If price breaks below 78.6%: trend may be broken, EXIT

**Best For:** PIDILITIND, DMART, TITAN, NESTLEIND

---

### 5. 📉 RSI Divergence (Counter-Trend Reversal)

**Type:** Reversal | **Hold:** 5–12 days

**How it works:**
A bullish RSI divergence occurs when price makes a **new lower low** but RSI makes a **higher low** — this means selling momentum is weakening. Combined with a key support level, this is a high-probability reversal signal.

**Divergence Detection:**
- **Bullish divergence**: Price lower low + RSI higher low → BUY signal
- **Bearish divergence**: Price higher high + RSI lower high → SHORT signal (not used in long-only mode)

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| Bullish RSI divergence | +40+ | Core reversal signal |
| Price near key support | +20 | Divergence is reliable |
| RSI below 30 | +20 | Strong reversal potential |
| MACD histogram rising | +15 | Momentum confirming |
| HTF above EMA200 | +10 | Long-term trend intact |

**Entry Rules:**
- RSI must show clear bullish divergence on LTF
- RSI should be below 40 (ideally below 30)
- Price must be at or near a key support level
- MACD histogram should be turning upward
- MANDATORY: Require 2+ confirmations before entering

**Exit Rules:**
- 🎯 Target: RSI reaches 60–65 / next resistance
- 🎯 Target: 3.5 × ATR above entry
- 🛑 SL: Below the swing low that created the divergence
- ⚠️ Counter-trend trade: Use smaller position size (50% normal)
- Tighten stops aggressively once profitable

**Best For:** HCLTECH, WIPRO, SUNPHARMA during corrections

---

### 6. 🌡️ Bollinger Band Squeeze (Volatility Breakout)

**Type:** Volatility Breakout | **Hold:** 3–10 days

**How it works:**
Bollinger Bands narrow (squeeze) when volatility is low. This consolidation is followed by an explosive move. The strategy waits for the squeeze and then trades the breakout in the direction of the HTF trend.

**Squeeze Phases:**
1. **Squeeze forming**: Bands narrow, bandwidth below average
2. **Squeeze active**: Bandwidth near 20-period low
3. **Breakout**: Price closes outside the band with volume surge
4. **Expansion**: Target upper band + extension

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| Active squeeze (bandwidth at low) | +30 | Setup ready |
| Price above upper band | +30 | Bullish breakout confirmed |
| HTF uptrend | +15 | Aligned with trend |
| RSI 50–75 | +15 | Momentum supporting |
| Volume ≥ 2.0x | +20 | Explosive breakout |

**Entry Rules:**
- Bollinger bandwidth must be near 20-period low
- Price closes ABOVE the upper Bollinger Band
- HTF trend must be bullish (price above EMA50 on daily)
- RSI between 50–75 (momentum confirms direction)
- Volume spike ≥ 1.5x on breakout candle

**Exit Rules:**
- 🎯 Target: Upper band + 1.5 × band width above
- 🛑 SL: Below middle band (20 SMA) −0.3 ATR
- 🔁 Trail: Move SL to middle band as price rises
- ❌ If price re-enters the bands after breakout: reduce position

**Best For:** ADANIENT, TATASTEEL, COALINDIA during quiet phases

---

## 📊 Scoring System

### Final Score Calculation
```
Final Score = (Strategy Score × 0.4) + (AI Score × 0.6)
```

| Score | Category | Action |
|-------|----------|--------|
| ≥ 80 | 🔥 STRONG BUY | Full position, send alert |
| 60–79 | ✅ BUY | Standard position |
| 40–59 | ⚠️ WATCH | Reduced position / wait |
| < 40 | ❌ AVOID | Skip this trade |

Telegram alerts are sent for scores ≥ 70 (configurable in sidebar).

---

## 🛡️ Risk Management Rules

1. **Max risk per trade**: 1–2% of total capital
2. **Minimum R:R**: 1:2 (never take a trade with less)
3. **Stop-loss is mandatory**: Set it BEFORE entering the trade
4. **Position sizing**: Use ATR to normalize risk across volatility regimes
5. **Diversification**: Max 5 open trades at once
6. **Sector exposure**: Max 2 trades in same sector

```python
# Position sizing formula
position_size = (capital × risk_pct) / (entry_price - sl_price)

# Example:
# Capital = ₹1,00,000 | Risk = 1% = ₹1,000
# Entry = ₹500 | SL = ₹480 | Risk per share = ₹20
# Position size = 1000 / 20 = 50 shares
```

---

## ⏰ Best Timeframe Combinations

| Strategy | HTF | LTF | Swing Hold |
|----------|-----|-----|------------|
| RSI + MACD Combo | Daily | 1h | 5–15 days |
| EMA Crossover | Daily | 1h / 4h | 10–30 days |
| S&R Breakout | Daily | 1h | 7–20 days |
| Fibonacci Retracement | Daily | 1h | 7–15 days |
| RSI Divergence | Daily | 1h | 5–12 days |
| Bollinger Squeeze | Daily | 4h / 1h | 3–10 days |
| Supertrend + VWAP | Daily | 1h | 5–20 days |
| Price & Volume Divergence | Daily | 1h | 7–15 days |
| Price & RSI Divergence | Daily | 1h | 5–15 days |
| Market Condition Scanner | Daily | 1h | Pre-trade check |

---

### 7. 🚀 Supertrend + VWAP

**Type:** Trend + Institutional Confluence | **Hold:** 5–20 days

**How it works:**
Supertrend is a dynamic ATR-based trailing stop that flips between bullish and bearish. VWAP (Volume Weighted Average Price) is the price institutions use as their benchmark — price above VWAP = institutions are in profit. Both must agree for entry.

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| HTF Supertrend fresh bullish flip | +35 | Trend confirmed — prime setup |
| HTF Supertrend bullish (ongoing) | +20 | Uptrend active |
| LTF Supertrend fresh bullish flip | +30 | Entry trigger |
| Price just above VWAP (<1%) | +25 | Ideal institutional entry zone |
| VWAP rising | +10 | Accumulation ongoing |
| RSI 45–70 | +10 | Momentum healthy |
| Volume ≥ 1.5x | +10 | Participation confirmed |

**Entry Rules:**
- Supertrend must be BULLISH on HTF (daily) — trend direction
- Supertrend flips BULLISH on LTF — this is the entry trigger
- Price must be ABOVE VWAP (within 1–3% is the ideal zone)
- VWAP should be rising (institutional demand increasing)
- RSI between 45–70

**Exit Rules:**
- 🎯 Target: 3 × ATR above entry
- 🛑 SL: Supertrend line on LTF (dynamic trailing stop — moves up daily)
- 🔁 Trail: Adjust SL every day to the new Supertrend value
- ❌ Supertrend flips RED → EXIT immediately
- ❌ Price closes below VWAP 2 consecutive candles → EXIT

**Best For:** All liquid NSE stocks, especially HDFCBANK, ICICIBANK, BAJFINANCE

---

### 8. 🧠 Price & Volume Divergence

**Type:** Smart Money Detection | **Hold:** 7–15 days

**How it works:**
Institutions cannot hide their buying in volume. When price makes new lows but OBV (On Balance Volume) makes higher lows, smart money is accumulating while retail panics. This strategy detects that footprint.

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| Bullish P/V divergence + declining sell volume | +45 | Smart money accumulating — strongest signal |
| Bullish P/V divergence only | +30 | OBV diverging from price |
| Sell volume declining | +15 | Bearish conviction weakening |
| OBV rising consistently (5 + 10 bar) | +20 | Accumulation confirmed |
| Up-candle volume ≥ 1.5x down-candle | +15 | Buyers dominant |
| Price near HTF support | +10 | Divergence at key level |

**Entry Rules:**
- Price makes lower low (looks bearish to retail)
- OBV makes higher low (institutions are actually buying)
- Volume on down candles is DECREASING (sellers losing steam)
- OBV trending up on both 5-bar and 10-bar lookback
- Up-candle volume exceeds down-candle volume ratio

**Exit Rules:**
- 🎯 Target: 3.5 × ATR above entry / next resistance
- 🛑 SL: Below swing low (−0.5 ATR buffer)
- ❌ OBV declines sharply after entry → distribution starting → EXIT
- ❌ Bearish P/V divergence (price HH + OBV LH) → EXIT

**Best For:** SBIN, ONGC, COALINDIA, BPCL (high-volume PSU stocks where institutional activity is detectable)

---

### 9. 🔬 Price & RSI Divergence (Enhanced)

**Type:** Multi-window Momentum Reversal | **Hold:** 5–15 days

**How it works:**
The most sophisticated divergence system — simultaneously scans 3 lookback windows (5, 8, 13 bars) for 4 types of divergence, adds Stochastic RSI for extreme readings, and requires candlestick pattern confirmation. Multi-window alignment dramatically increases reliability.

**4 Divergence Types:**
| Type | Price | RSI | Signal |
|------|-------|-----|--------|
| Classic Bullish | Lower Low | Higher Low | Reversal UP ↑ |
| Classic Bearish | Higher High | Lower High | Reversal DOWN ↓ |
| Hidden Bullish | Higher Low | Lower Low | Trend continuation UP ↑ |
| Hidden Bearish | Lower High | Higher High | Trend continuation DOWN ↓ |

**Signal Logic:**
| Signal | Score | Meaning |
|--------|-------|---------|
| Classic bullish divergence | +40–60 | Core reversal signal |
| Hidden bullish divergence | +25–40 | Trend continuation |
| 2+ windows confirm | +15 | HIGH reliability bonus |
| RSI < 30 | +20 | Deeply oversold |
| StochRSI < 20 | +15 | Double oversold |
| MACD histogram rising 3 bars | +15 | Momentum confirmed |
| Hammer / Bullish Engulfing | +12–15 | Candlestick confirmation |
| HTF above EMA200 | +10 | Long-term structure intact |

**Entry Rules:**
- Classic or Hidden BULLISH divergence in at least 1 window
- RSI below 50 (ideally below 40)
- Stochastic RSI below 20 (double oversold)
- MACD histogram turning up (3 consecutive bars = strongest)
- Confirmation candlestick: Hammer, Bullish Engulfing, or strong recovery

**Exit Rules:**
- 🎯 Target: Recent resistance level / 3.5 × ATR above entry
- 🛑 SL: 2 × ATR below entry (wider — reversal trades need room)
- ❌ RSI makes new lower low after entry → divergence failed → EXIT
- ❌ Classic bearish divergence appears → EXIT
- Multi-window (2+ windows) → larger position size
- Single-window → standard/reduced position size

**Best For:** Any liquid NSE stock at oversold extremes — HCLTECH, WIPRO, SUNPHARMA, DRREDDY during corrections

---

### 10. 🎛️ Market Condition Scanner

**Type:** OB / OS / Fair Value Assessment + S/R Zone Mapping | **Hold:** Informational (use before any trade)

**How it works:**
A 6-indicator consensus engine that scores a ticker from −100 (deeply oversold) to +100 (deeply overbought) and simultaneously maps ALL nearby support and resistance zones from multiple sources — pivots, Fibonacci levels, psychological levels, and dynamic EMAs — to give you a complete picture of where the stock sits in its range.

**6-Indicator System:**
| Indicator | Max Weight | What It Measures |
|-----------|-----------|-----------------|
| RSI (14) | ±25 pts | Momentum extreme |
| Stochastic RSI | ±20 pts | Normalized RSI — compressed / extended |
| Bollinger Band Position | ±20 pts | Statistical price extreme (0 = lower, 1 = upper band) |
| Price vs VWAP | ±15 pts | Institutional deviation from fair value |
| EMA Stack (20/50/200) | ±10 pts | Trend structure alignment |
| EMA20 Extension % | ±10 pts | Mean reversion risk gauge |

**Condition Scale:**
| Score | Label | Recommended Action |
|-------|-------|--------------------|
| +70 to +100 | 🔴 OVERBOUGHT | Avoid new longs — wait for pullback |
| +30 to +69 | 🟠 MILDLY OVERBOUGHT | Caution — tight stop, strong momentum only |
| −29 to +29 | 🟢 FAIR VALUE | Ideal entry zone — best risk:reward |
| −30 to −69 | 🔵 MILDLY OVERSOLD | Watch — prepare buy levels |
| −70 to −100 | 💜 OVERSOLD | Strong bounce candidate — wait for candle confirmation |

**S/R Zone Detection (4 sources merged):**
1. **Swing Pivots** — Pivot highs and lows from the last 120 bars (only zones with 2+ touches kept)
2. **Fibonacci Levels** — 23.6%, 38.2%, 50%, 61.8%, 78.6% retracements of the last major swing
3. **Dynamic EMAs** — EMA20, EMA50, EMA200 and VWAP as real-time S/R
4. **Psychological Levels** — Round numbers proportional to the stock's price magnitude

**Strength Rating per Zone:**
- Each zone is scored 0–100% based on number of touches (more touches = stronger zone)
- 3+ touches = strongest zones (score 80–100%)
- Fibonacci + pivot confluence = highest reliability

**Trade Setup Logic:**
| Condition | Near Support? | Setup Quality |
|-----------|--------------|---------------|
| 💜 OVERSOLD | Within 3% of S1 | 🔥 HIGH PROBABILITY LONG |
| 💜 OVERSOLD | Within 6% of S1 | ✅ WATCH — set buy alert |
| 🟢 FAIR VALUE | Within 2% of S1 | ✅ GOOD R:R ENTRY |
| 🟠 MILDLY OB | Near resistance | ⛔ AVOID — wait for pullback |
| 🔴 OVERBOUGHT | Any | ❌ NO NEW LONGS |

**Rich UI Features in Dashboard:**
- Colour-coded condition badge (red/orange/green/blue/purple)
- Support zones shown as green cards with distance % and strength bar
- Resistance zones shown as red cards with distance % and strength bar
- Key levels grid (VWAP, EMA20/50/200, BB Upper/Lower, ATR)
- Chart overlays: all S/R lines + VWAP plotted directly on the candle chart
- Custom Telegram alert format with all zones included

**Best For:** Use on ANY ticker as a pre-trade scan. Works best as a filter before running other strategies — if the scanner says FAIR VALUE or OVERSOLD at a strong support, then proceed with RSI+MACD, EMA Crossover, or Fibonacci entry strategies.

---

## ⚠️ Important Disclaimers

> This tool is for **educational and informational purposes only**.
> It does NOT constitute financial advice.
> Past performance of technical strategies does not guarantee future results.
> Always consult a SEBI-registered financial advisor before investing.
> The Indian stock market involves significant risk of loss.
> Never invest money you cannot afford to lose.