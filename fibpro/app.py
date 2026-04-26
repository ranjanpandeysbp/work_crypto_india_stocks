import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from groww_data import fetch_ohlc
from strategy import analyze_symbol, STRATEGIES
from ai_filter import analyze_trade
from alerts import send_alert
from logger import log_trade, load_trades

st.set_page_config(
    page_title="AI Swing Trader — NSE",
    layout="wide",
    page_icon="📊"
)

# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")

    # Strategy selector
    strategy_name = st.selectbox(
        "🎯 Select Strategy",
        list(STRATEGIES.keys()),
        help="Choose which swing trading strategy to run"
    )

    # Strategy info cards
    strategy_info = {
        "RSI + MACD Combo": {
            "icon": "🔁",
            "type": "Momentum",
            "hold": "5–15 days",
            "accuracy": "High",
            "best_for": "Trending large-caps (Reliance, INFY, TCS)"
        },
        "EMA Crossover": {
            "icon": "📈",
            "type": "Trend Following",
            "hold": "10–30 days",
            "accuracy": "High in trends",
            "best_for": "Strongly trending Nifty 50 stocks"
        },
        "S&R Breakout": {
            "icon": "🧱",
            "type": "Breakout",
            "hold": "7–20 days",
            "accuracy": "High (if volume confirmed)",
            "best_for": "F&O stocks, Bank Nifty components"
        },
        "Fibonacci Retracement": {
            "icon": "🎯",
            "type": "Pullback",
            "hold": "7–15 days",
            "accuracy": "Medium–High",
            "best_for": "Mid-caps with clean swings"
        },
        "RSI Divergence": {
            "icon": "📉",
            "type": "Counter-trend / Reversal",
            "hold": "5–12 days",
            "accuracy": "Medium (needs confirmation)",
            "best_for": "Beaten-down large-caps at support"
        },
        "Bollinger Band Squeeze": {
            "icon": "🌡️",
            "type": "Volatility Breakout",
            "hold": "3–10 days",
            "accuracy": "High after tight squeeze",
            "best_for": "Mid-caps in low-volatility phases"
        },
        "Supertrend + VWAP": {
            "icon": "🚀",
            "type": "Trend + Institutional Confluence",
            "hold": "5–20 days",
            "accuracy": "Very High (dual confirmation)",
            "best_for": "All liquid NSE stocks, esp. Bank Nifty components"
        },
        "Price & Volume Divergence": {
            "icon": "🧠",
            "type": "Smart Money Detection",
            "hold": "7–15 days",
            "accuracy": "High at key support zones",
            "best_for": "Large-caps being accumulated (SBIN, ONGC, COAL)"
        },
        "Price & RSI Divergence": {
            "icon": "🔬",
            "type": "Multi-window Momentum Reversal",
            "hold": "5–15 days",
            "accuracy": "Very High (multi-window + Stoch RSI)",
            "best_for": "Any liquid NSE stock at oversold extremes"
        },
        "Market Condition Scanner": {
            "icon": "🎛️",
            "type": "OB / OS / Fair Value + S/R Zones",
            "hold": "Informational — any hold period",
            "accuracy": "Very High (6-indicator consensus)",
            "best_for": "Any ticker — use before every trade as pre-trade check"
        },
    }

    info = strategy_info.get(strategy_name, {})
    if info:
        st.markdown("---")
        st.markdown(f"### {info['icon']} Strategy Details")
        st.markdown(f"**Type:** {info['type']}")
        st.markdown(f"**Avg Hold:** {info['hold']}")
        st.markdown(f"**Accuracy:** {info['accuracy']}")
        st.markdown(f"**Best for:** {info['best_for']}")

    st.markdown("---")

    # Score thresholds
    st.markdown("### 🎚️ Score Thresholds")
    strong_buy_threshold  = st.slider("🔥 Strong Buy (≥)", 60, 95, 80)
    buy_threshold         = st.slider("✅ Buy (≥)", 40, 79, 60)
    watch_threshold       = st.slider("⚠️ Watch (≥)", 20, 59, 40)
    alert_threshold       = st.slider("🔔 Send Alert (≥)", 50, 95, 70)

    st.markdown("---")
    enable_ai = st.toggle("🤖 Enable AI Filter", value=True)
    enable_alerts = st.toggle("📲 Enable Telegram Alerts", value=True)

# ─── Main ───────────────────────────────────────────────────────────────────
st.title("📊 AI Swing Trading Dashboard — NSE/BSE")
st.caption(f"Running strategy: **{strategy_name}**")

col_sym, col_tf = st.columns([3, 1])

with col_sym:
    symbols_input = st.text_area(
        "Enter Symbols (comma separated)",
        "RELIANCE,INFY,TCS,HDFCBANK,AXISBANK",
        height=68
    )

with col_tf:
    timeframe = st.selectbox(
        "LTF Timeframe",
        ["5m", "10m", "1h", "4h", "1d", "1w"],
        index=2,
        help="Lower timeframe for entry signals"
    )

symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

col1, col2, col3 = st.columns(3)
scan_btn     = col1.button("🔍 Scan Market", use_container_width=True)
show_logs    = col2.button("📜 Trade History", use_container_width=True)
clear_btn    = col3.button("🗑️ Clear Results", use_container_width=True)

st.markdown("---")

# ─── Strategy Entry/Exit Guide ───────────────────────────────────────────────
with st.expander(f"📖 {strategy_name} — Entry & Exit Guide", expanded=False):
    guides = {
        "RSI + MACD Combo": """
**Entry Criteria:**
- ✅ Price above EMA50 on daily chart (HTF uptrend)
- ✅ RSI between 30–45 on LTF (oversold bounce)
- ✅ MACD bullish crossover (MACD line crosses above signal)
- ✅ Volume ≥ 1.5x average

**Exit Criteria:**
- 🎯 Target: RSI reaches 65–70 (overbought zone)
- 🎯 Target: MACD histogram turns negative
- 🛑 Stop-Loss: 1.5 × ATR below entry price
- ⏳ Time-based exit: If trade doesn't move in 7 days, exit

**Risk Management:**
- Risk per trade: Max 1–2% of capital
- Minimum Risk:Reward = 1:2
- Position sizing: Use ATR to size positions
""",
        "EMA Crossover": """
**Entry Criteria:**
- ✅ EMA20 crosses above EMA50 on LTF (golden cross)
- ✅ Price > EMA9 > EMA20 > EMA50 (perfect stack)
- ✅ EMA20 slope is positive and rising
- ✅ HTF: Price above EMA50 (trend aligned)
- ✅ Volume confirms on breakout

**Exit Criteria:**
- 🎯 Target: 2.5 × ATR above entry
- 🛑 Stop-Loss: Below EMA50 on LTF (−0.5 ATR buffer)
- 🛑 Trail stop: Move SL to EMA20 as trade progresses
- ❌ Exit if EMA20 crosses back below EMA50

**Risk Management:**
- Best in clear trending markets (avoid choppy/sideways)
- Avoid during major news events (budget, RBI policy)
""",
        "S&R Breakout": """
**Entry Criteria:**
- ✅ Price closes ABOVE key resistance (20-period swing high)
- ✅ Volume ≥ 1.5x (mandatory — no volume = false breakout)
- ✅ Consolidation of 3–5 candles before breakout (tight base)
- ✅ RSI between 50–70 (momentum confirming)
- ✅ HTF uptrend supports the breakout direction

**Exit Criteria:**
- 🎯 Target: Next major resistance level / 3 × ATR
- 🛑 Stop-Loss: Below the breakout candle's low (−0.3 ATR buffer)
- ⚠️ If price closes back below the breakout level — EXIT immediately
- 🔁 Re-test of breakout level as support = add to position

**Risk Management:**
- Volume is NON-NEGOTIABLE for breakouts — skip if low volume
- Avoid breakouts near major resistance (lifetime highs) without institutional volume
""",
        "Fibonacci Retracement": """
**Entry Criteria:**
- ✅ Strong prior uptrend (HTF price above EMA50)
- ✅ Price pulls back to 38.2%, 50%, or 61.8% Fibonacci level
- ✅ RSI recovering (35–55) and turning upward
- ✅ Volume declining during pullback (healthy retracement)
- ✅ Confirmation candle (bullish engulfing/hammer) at Fib level

**Exit Criteria:**
- 🎯 Target: Previous swing high (100% retracement)
- 🎯 Extended target: 127.2% Fibonacci extension
- 🛑 Stop-Loss: Below 78.6% Fib level (−0.5 ATR buffer)
- ❌ If price breaks below 78.6% Fib, trend may be broken — exit

**Risk Management:**
- 61.8% (Golden Ratio) is the most reliable — give it higher position sizing
- 38.2% = small position (trend may continue without deep pullback)
""",
        "RSI Divergence": """
**Entry Criteria:**
- ✅ Bullish divergence: Price makes LOWER LOW, RSI makes HIGHER LOW
- ✅ RSI below 40 (ideally below 30 for strongest signal)
- ✅ Price near key support level (swing low, EMA200)
- ✅ MACD histogram turning upward (confirming momentum shift)
- ✅ HTF above EMA200 (don't fight the long-term trend)

**Exit Criteria:**
- 🎯 Target: RSI reaches 60–65 / next resistance
- 🎯 Target: 3.5 × ATR above entry
- 🛑 Stop-Loss: Below the swing low that created the divergence
- ⚠️ This is a counter-trend trade — keep position size smaller

**Risk Management:**
- Always require at LEAST 2 confirmations (RSI div + MACD + support)
- Divergence without support level = low probability
- Tighten stops aggressively once profitable
""",
        "Bollinger Band Squeeze": """
**Entry Criteria:**
- ✅ Bollinger Band bandwidth near 20-period low (tight squeeze)
- ✅ Price closes ABOVE upper Bollinger Band (bullish breakout)
- ✅ HTF uptrend (price above EMA50 on daily)
- ✅ RSI between 50–75 (momentum confirms direction)
- ✅ Volume spike ≥ 1.5x on breakout candle

**Exit Criteria:**
- 🎯 Target: Upper band + 1.5 × band width above
- 🛑 Stop-Loss: Below the middle band (20 SMA) −0.3 ATR
- 🔁 Trail stop: Move SL to middle band as price rises
- ❌ If price re-enters the bands after breakout — exit or reduce

**Risk Management:**
- The TIGHTER the squeeze, the bigger the expected move
- After a long squeeze (10+ candles), expect explosive moves
- Don't enter during earnings week without extra caution
""",
        "Supertrend + VWAP": """
**How it Works:**
Supertrend is a dynamic trailing stop based on ATR — it flips from bearish to bullish when price decisively breaks above it. VWAP (Volume Weighted Average Price) is the institutional benchmark — price above VWAP = institutions are in profit, supporting the move.

**Entry Criteria:**
- ✅ Supertrend flips BULLISH on HTF (daily) — primary trend confirmed
- ✅ Supertrend flips BULLISH on LTF — entry trigger
- ✅ Price is ABOVE VWAP (within 1–3% is ideal sweet spot)
- ✅ VWAP is rising (institutions actively accumulating)
- ✅ RSI between 45–70 (momentum healthy, not overbought)

**Exit Criteria:**
- 🎯 Target: 3 × ATR above entry
- 🛑 Stop-Loss: Supertrend line on LTF (dynamic — trails price up)
- 🔁 Trail: As Supertrend line rises, move your SL up with it automatically
- ❌ If Supertrend flips RED (bearish) — exit immediately, no exceptions
- ❌ If price closes below VWAP on 2 consecutive candles — exit

**Risk Management:**
- The Supertrend SL is DYNAMIC — adjust it every day as the line moves up
- Fresh Supertrend flip = highest probability entry (score: +35)
- Avoid entering when price is >3% above VWAP (overextended)
- Best with 1h LTF + Daily HTF combination
""",
        "Price & Volume Divergence": """
**How it Works:**
Smart money (institutions) can't hide their footprints in volume. When price makes new lows but OBV (On Balance Volume) makes higher lows — institutions are quietly BUYING while retail sells. This is called accumulation divergence.

**Bullish Setup (what we detect):**
- Price makes LOWER LOW (looks bearish to retail)
- OBV makes HIGHER LOW (institutions are buying the dip)
- Volume on DOWN candles is DECREASING (sellers losing conviction)
- Volume on UP candles is INCREASING (buyers gaining power)

**Entry Criteria:**
- ✅ Bullish Price-Volume divergence (price LL + OBV HL)
- ✅ Selling volume declining on recent down moves
- ✅ OBV rising on short-term basis (5 and 10 bar slope)
- ✅ Up-candle volume ≥ 1.5x down-candle volume
- ✅ Price near HTF support zone

**Exit Criteria:**
- 🎯 Target: 3.5 × ATR above entry / next resistance
- 🛑 Stop-Loss: Below swing low (−0.5 ATR buffer)
- ❌ If OBV starts declining sharply — distribution is starting, EXIT
- ❌ If bearish P/V divergence appears (price HH + OBV LH) — EXIT

**Risk Management:**
- Works best on high-liquidity stocks (Nifty 50, Nifty Next 50)
- Combine with HTF uptrend for highest probability
- This is a LEADING indicator — gives early entry before price reverses
""",
        "Price & RSI Divergence": """
**How it Works:**
The most comprehensive RSI divergence system — scans 3 different lookback windows (5, 8, 13 bars) simultaneously and detects 4 types of divergences. Also adds Stochastic RSI and candlestick patterns as extra filters.

**4 Types of Divergence:**
| Type | Price | RSI | Signal |
|------|-------|-----|--------|
| Classic Bullish | Lower Low | Higher Low | Reversal UP ↑ |
| Classic Bearish | Higher High | Lower High | Reversal DOWN ↓ |
| Hidden Bullish | Higher Low | Lower Low | Continuation UP ↑ |
| Hidden Bearish | Lower High | Higher High | Continuation DOWN ↓ |

**Entry Criteria:**
- ✅ Classic or Hidden BULLISH divergence (1+ windows)
- ✅ RSI below 50 (ideally below 40)
- ✅ Stochastic RSI below 20 (double oversold)
- ✅ MACD histogram rising (3 consecutive bars = strongest)
- ✅ Hammer / Bullish Engulfing candle at divergence point
- ✅ HTF above EMA200 (long-term trend intact)

**Exit Criteria:**
- 🎯 Target: Nearest recent resistance / 3.5 × ATR above entry
- 🛑 Stop-Loss: 2 × ATR below entry (wider for reversal trades)
- ❌ If RSI makes a NEW lower low after entry — divergence failed, EXIT
- ❌ Classic BEARISH divergence appears — EXIT immediately

**Risk Management:**
- Multi-window confirmation (2+ windows align) = HIGHER position size
- Single-window divergence = standard/reduced position size
- Always wait for a confirmation candle (don't anticipate — wait for it)
- Counter-trend (vs EMA200) = reduce position size by 50%
""",
        "Market Condition Scanner": """
**Purpose:**
Use this as your **pre-trade checklist** before entering any position. It tells you exactly where a stock stands right now — is it cheap, expensive, or fairly priced? And where are the nearest zones to set your stops and targets?

**6-Indicator Consensus System:**
| Indicator | Weight | Reads |
|-----------|--------|-------|
| RSI (14) | 25 pts | Momentum extreme |
| Stochastic RSI | 20 pts | RSI compressed/extended |
| Bollinger Position | 20 pts | Statistical price extreme |
| Price vs VWAP | 15 pts | Institutional deviation |
| EMA Stack | 10 pts | Trend structure |
| EMA20 Extension | 10 pts | Mean reversion risk |

**Condition Scale:**
| Score | Condition | What to Do |
|-------|-----------|------------|
| +70 to +100 | 🔴 OVERBOUGHT | Avoid new longs, wait for pullback |
| +30 to +69 | 🟠 MILDLY OVERBOUGHT | Only enter with strong momentum; tight stop |
| -29 to +29 | 🟢 FAIR VALUE | Best zone for entries |
| -30 to -69 | 🔵 MILDLY OVERSOLD | Watch for reversal signal |
| -70 to -100 | 💜 OVERSOLD | Strong bounce candidate; wait for candle |

**S/R Zone Sources (all merged):**
- Swing pivot highs/lows (120-bar lookback, 2+ touches required)
- Psychological round-number levels
- Fibonacci retracement levels (23.6%–78.6%)
- Dynamic EMA lines (EMA20, EMA50, EMA200)
- VWAP as institutional anchor

**Best Setup:** OVERSOLD + at strong Support → highest probability long entry.
"""
    }
    st.markdown(guides.get(strategy_name, "Select a strategy to view its guide."))

# ─── SCAN ───────────────────────────────────────────────────────────────────
if scan_btn:
    results = []
    progress = st.progress(0, text="Scanning symbols...")

    for i, symbol in enumerate(symbols):
        progress.progress((i) / len(symbols), text=f"Scanning {symbol}...")

        df_daily = fetch_ohlc(symbol, "day", 100)
        df_ltf   = fetch_ohlc(symbol, timeframe, 100)

        if df_daily is None or df_ltf is None:
            st.warning(f"❌ {symbol}: Data fetch failed")
            continue

        st.info(f"📊 {symbol} — Daily: {len(df_daily)} candles | {timeframe}: {len(df_ltf)} candles")

        trade = analyze_symbol(df_daily, df_ltf, strategy_name=strategy_name)

        if trade:
            # ── Rich UI for Market Condition Scanner ───────────────────────
            if strategy_name == "Market Condition Scanner" and "condition" in trade:
                st.markdown(f"### 🎛️ {symbol} — Market Condition Report")

                cond      = trade["condition"]
                c_score   = trade["cond_score"]
                action    = trade["action"]
                kl        = trade.get("key_levels", {})
                sups      = trade.get("nearest_supports", [])
                ress      = trade.get("nearest_resistances", [])
                curr_p    = trade["Entry"]

                # Condition badge
                cond_color = {
                    "🔴": "#ff4444", "🟠": "#ff8800",
                    "🟢": "#00cc66", "🔵": "#3399ff", "💜": "#9966ff"
                }
                badge_color = next(
                    (v for k, v in cond_color.items() if k in cond), "#888"
                )

                col_cond, col_score, col_action = st.columns([2, 1, 3])
                with col_cond:
                    st.markdown(
                        f'<div style="background:{badge_color}22;border:2px solid {badge_color};'
                        f'border-radius:8px;padding:12px;text-align:center;">'
                        f'<b style="font-size:1.2em">{cond}</b></div>',
                        unsafe_allow_html=True
                    )
                with col_score:
                    st.metric("Condition Score", f"{c_score:+d}", delta=None)
                with col_action:
                    st.info(f"💡 {action}")

                st.markdown("---")

                # Support & Resistance table
                sr_col1, sr_col2 = st.columns(2)
                with sr_col1:
                    st.markdown("#### 🟢 Nearest Support Zones")
                    if sups:
                        for j, s in enumerate(sups, 1):
                            dist = (curr_p - s["level"]) / curr_p * 100
                            bar  = "█" * (s["strength"] // 20)
                            st.markdown(
                                f'<div style="background:#00cc6622;border-left:4px solid #00cc66;'
                                f'padding:8px;margin:4px 0;border-radius:4px;">'
                                f'<b>S{j}: ₹{s["level"]:.2f}</b> &nbsp;|&nbsp; '
                                f'{dist:.1f}% below &nbsp;|&nbsp; '
                                f'Strength: {bar} {s["strength"]}% &nbsp;|&nbsp; '
                                f'<i>{s.get("label","")}</i></div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.warning("No clear support zones found")

                with sr_col2:
                    st.markdown("#### 🔴 Nearest Resistance Zones")
                    if ress:
                        for j, r in enumerate(ress, 1):
                            dist = (r["level"] - curr_p) / curr_p * 100
                            bar  = "█" * (r["strength"] // 20)
                            st.markdown(
                                f'<div style="background:#ff444422;border-left:4px solid #ff4444;'
                                f'padding:8px;margin:4px 0;border-radius:4px;">'
                                f'<b>R{j}: ₹{r["level"]:.2f}</b> &nbsp;|&nbsp; '
                                f'{dist:.1f}% above &nbsp;|&nbsp; '
                                f'Strength: {bar} {r["strength"]}% &nbsp;|&nbsp; '
                                f'<i>{r.get("label","")}</i></div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.warning("No clear resistance zones found")

                st.markdown("---")

                # Key levels grid
                st.markdown("#### 📏 Key Price Levels")
                kl_cols = st.columns(4)
                level_items = [
                    ("CMP", curr_p, "#ffffff"),
                    ("VWAP", kl.get("vwap"), "#ffcc00"),
                    ("EMA20", kl.get("ema20"), "#ff8800"),
                    ("EMA50", kl.get("ema50"), "#3399ff"),
                    ("EMA200", kl.get("ema200"), "#cc44ff"),
                    ("BB Upper", kl.get("bb_upper"), "#ff4444"),
                    ("BB Lower", kl.get("bb_lower"), "#00cc66"),
                    ("ATR(14)", kl.get("atr"), "#888888"),
                ]
                for idx, (lbl, val, color) in enumerate(level_items):
                    with kl_cols[idx % 4]:
                        if val is not None:
                            st.markdown(
                                f'<div style="background:#1a1a2e;border:1px solid {color}44;'
                                f'border-radius:6px;padding:8px;margin:2px;">'
                                f'<span style="color:{color};font-size:0.75em">{lbl}</span><br>'
                                f'<b style="font-size:1.1em">₹{val:.2f}</b></div>',
                                unsafe_allow_html=True
                            )

                st.markdown("---")

                # Full signal log in expander
                with st.expander(f"📋 Full Indicator Breakdown — {symbol}"):
                    for sig in trade.get("signals", []):
                        st.text(sig)

            else:
                with st.expander(f"🔍 {symbol} — {strategy_name} Signals"):
                    for sig in trade.get("signals", []):
                        st.write(sig)
                    st.write(f"**Strategy Score: {trade['strategy_score']}/100**")

            ai_score = 50  # default if AI disabled
            ai_raw   = "AI filter disabled"

            if enable_ai:
                ai = analyze_trade(symbol, trade)
                ai_score = ai["ai_score"]
                ai_raw   = ai["raw"]

                final_score = int(trade["strategy_score"] * 0.4 + ai_score * 0.6)
            else:
                final_score = trade["strategy_score"]

            if final_score >= strong_buy_threshold:
                category = "🔥 STRONG BUY"
            elif final_score >= buy_threshold:
                category = "✅ BUY"
            elif final_score >= watch_threshold:
                category = "⚠️ WATCH"
            else:
                category = "❌ AVOID"

            rr = round(
                (trade["Target"] - trade["Entry"]) / max(trade["Entry"] - trade["SL"], 0.01),
                2
            )

            trade_data = {
                "Symbol": symbol,
                "Strategy": strategy_name,
                "Entry": trade["Entry"],
                "SL": trade["SL"],
                "Target": trade["Target"],
                "R:R": f"1:{rr}",
                "Strategy Score": trade["strategy_score"],
                "AI Score": ai_score,
                "Final Score": final_score,
                "Category": category,
                "AI Reason": ai_raw,
                # Market Condition Scanner extras (used for chart rendering)
                "condition":              trade.get("condition", ""),
                "cond_score":             trade.get("cond_score", ""),
                "nearest_supports_raw":   trade.get("nearest_supports", []),
                "nearest_resistances_raw":trade.get("nearest_resistances", []),
            }

            results.append(trade_data)

            if enable_alerts and final_score >= alert_threshold:
                if strategy_name == "Market Condition Scanner":
                    sups_txt = "\n".join(
                        f"  S{j+1}: ₹{s['level']:.2f} ({(trade['Entry']-s['level'])/trade['Entry']*100:.1f}% below)"
                        for j, s in enumerate(trade.get("nearest_supports", []))
                    ) or "  N/A"
                    res_txt = "\n".join(
                        f"  R{j+1}: ₹{r['level']:.2f} ({(r['level']-trade['Entry'])/trade['Entry']*100:.1f}% above)"
                        for j, r in enumerate(trade.get("nearest_resistances", []))
                    ) or "  N/A"
                    msg = f"""
🎛️ MARKET SCAN [{symbol}]
Condition: {trade.get('condition','')} (Score: {trade.get('cond_score',''):+})
Action: {trade.get('action','')}
CMP: ₹{trade['Entry']}
Support Zones:
{sups_txt}
Resistance Zones:
{res_txt}
SL: ₹{trade['SL']} | Target: ₹{trade['Target']} | R:R 1:{rr}
"""
                else:
                    msg = f"""
🚀 TRADE ALERT [{strategy_name}]
Symbol: {symbol}
Score: {final_score}/100 {category}
Entry: ₹{trade['Entry']}
SL:    ₹{trade['SL']}
Target:₹{trade['Target']}
R:R:   1:{rr}
"""
                success, error = send_alert(msg)
                if success:
                    st.success(f"📲 Alert sent: {symbol}")
                else:
                    st.warning(f"Telegram failed: {symbol} — {error}")

                log_trade(trade_data)
        else:
            st.warning(f"⚠️ {symbol}: Did not meet {strategy_name} criteria")

    progress.progress(1.0, text="Scan complete!")

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values(by="Final Score", ascending=False)

        st.success(f"📊 Found {len(results)} trade opportunity(s)")
        st.dataframe(df[["Symbol", "Strategy", "Entry", "SL", "Target", "R:R",
                          "Strategy Score", "AI Score", "Final Score", "Category"]],
                     use_container_width=True)

        st.markdown("---")
        selected = st.selectbox("📈 View Chart", df["Symbol"].tolist())
        df_chart = fetch_ohlc(selected, timeframe, 100)

        if df_chart is not None:
            fig = go.Figure()

            fig.add_trace(go.Candlestick(
                x=df_chart.index,
                open=df_chart['Open'],
                high=df_chart['High'],
                low=df_chart['Low'],
                close=df_chart['Close'],
                name=selected
            ))

            # Plot EMA20 and EMA50 on chart
            from strategy import ema as calc_ema, vwap as calc_vwap
            df_chart['EMA20'] = calc_ema(df_chart['Close'], 20)
            df_chart['EMA50'] = calc_ema(df_chart['Close'], 50)

            fig.add_trace(go.Scatter(
                x=df_chart.index, y=df_chart['EMA20'],
                line=dict(color='orange', width=1.5), name='EMA20'
            ))
            fig.add_trace(go.Scatter(
                x=df_chart.index, y=df_chart['EMA50'],
                line=dict(color='blue', width=1.5), name='EMA50'
            ))

            # For Market Condition Scanner: draw all S/R zones on the chart
            if strategy_name == "Market Condition Scanner":
                # Find the raw trade result for selected symbol from results list
                sel_result = next(
                    (r for r in results if r["Symbol"] == selected), None
                )
                if sel_result:
                    # Draw support zones (green shaded bands)
                    for sup in sel_result.get("nearest_supports_raw", []):
                        fig.add_hline(
                            y=sup["level"],
                            line_dash="dash", line_color="rgba(0,204,102,0.7)",
                            annotation_text=f"S: ₹{sup['level']:.2f} ({sup.get('label','')})",
                            annotation_font_color="rgba(0,204,102,1)"
                        )
                    # Draw resistance zones (red dashed lines)
                    for res in sel_result.get("nearest_resistances_raw", []):
                        fig.add_hline(
                            y=res["level"],
                            line_dash="dash", line_color="rgba(255,68,68,0.7)",
                            annotation_text=f"R: ₹{res['level']:.2f} ({res.get('label','')})",
                            annotation_font_color="rgba(255,68,68,1)"
                        )
                    # VWAP line
                    df_chart['VWAP'] = calc_vwap(df_chart)
                    fig.add_trace(go.Scatter(
                        x=df_chart.index, y=df_chart['VWAP'],
                        line=dict(color='yellow', width=1.5, dash='dot'),
                        name='VWAP'
                    ))
                    # Condition annotation
                    fig.add_annotation(
                        x=df_chart.index[-1], y=df_chart['Close'].iloc[-1],
                        text=sel_result.get("condition", ""),
                        showarrow=True, arrowhead=2,
                        font=dict(size=13, color="white"),
                        bgcolor="rgba(0,0,0,0.6)"
                    )
            else:
                # Standard: mark entry/SL/target
                sel_trade = df[df["Symbol"] == selected].iloc[0]
                fig.add_hline(y=sel_trade["Entry"], line_dash="dot",
                              line_color="green", annotation_text="Entry")
                fig.add_hline(y=sel_trade["SL"], line_dash="dot",
                              line_color="red", annotation_text="SL")
                fig.add_hline(y=sel_trade["Target"], line_dash="dot",
                              line_color="gold", annotation_text="Target")

            fig.update_layout(
                title=f"{selected} — {timeframe} | {strategy_name}",
                xaxis_rangeslider_visible=False,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        # Full AI Reason table
        with st.expander("🤖 Full AI Analysis"):
            for _, row in df.iterrows():
                st.markdown(f"**{row['Symbol']}** — Score: {row['Final Score']}")
                st.code(row["AI Reason"])
    else:
        st.warning(f"No trades found matching **{strategy_name}** criteria.")

# ─── HISTORY ─────────────────────────────────────────────────────────────────
if show_logs:
    trades = load_trades()
    if not trades.empty:
        st.subheader("📜 Trade History")

        # Filter by strategy
        if "Strategy" in trades.columns:
            strategy_filter = st.multiselect(
                "Filter by Strategy",
                options=trades["Strategy"].unique().tolist(),
                default=trades["Strategy"].unique().tolist()
            )
            trades = trades[trades["Strategy"].isin(strategy_filter)]

        st.dataframe(trades, use_container_width=True)

        # Stats
        if "Final Score" in trades.columns:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total Alerts", len(trades))
            col_b.metric("Avg Score", f"{trades['Final Score'].mean():.1f}")
            col_c.metric("Strong Buys", len(trades[trades["Final Score"] >= 80]))
    else:
        st.info("No trades logged yet.")