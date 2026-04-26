import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import traceback

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

# ─── Strategy info metadata ──────────────────────────────────────────────────
STRATEGY_INFO = {
    "RSI + MACD Combo": {
        "icon": "🔁", "type": "Momentum", "hold": "5–15 days",
        "accuracy": "High", "best_for": "Trending large-caps (Reliance, INFY, TCS)"
    },
    "EMA Crossover": {
        "icon": "📈", "type": "Trend Following", "hold": "10–30 days",
        "accuracy": "High in trends", "best_for": "Strongly trending Nifty 50 stocks"
    },
    "S&R Breakout": {
        "icon": "🧱", "type": "Breakout", "hold": "7–20 days",
        "accuracy": "High (if volume confirmed)", "best_for": "F&O stocks, Bank Nifty components"
    },
    "Fibonacci Retracement": {
        "icon": "🎯", "type": "Pullback", "hold": "7–15 days",
        "accuracy": "Medium–High", "best_for": "Mid-caps with clean swings"
    },
    "RSI Divergence": {
        "icon": "📉", "type": "Counter-trend / Reversal", "hold": "5–12 days",
        "accuracy": "Medium (needs confirmation)", "best_for": "Beaten-down large-caps at support"
    },
    "Bollinger Band Squeeze": {
        "icon": "🌡️", "type": "Volatility Breakout", "hold": "3–10 days",
        "accuracy": "High after tight squeeze", "best_for": "Mid-caps in low-volatility phases"
    },
    "Supertrend + VWAP": {
        "icon": "🚀", "type": "Trend + Institutional Confluence", "hold": "5–20 days",
        "accuracy": "Very High (dual confirmation)", "best_for": "All liquid NSE stocks"
    },
    "Price & Volume Divergence": {
        "icon": "🧠", "type": "Smart Money Detection", "hold": "7–15 days",
        "accuracy": "High at key support zones", "best_for": "Large-caps being accumulated"
    },
    "Price & RSI Divergence": {
        "icon": "🔬", "type": "Multi-window Momentum Reversal", "hold": "5–15 days",
        "accuracy": "Very High (multi-window + Stoch RSI)", "best_for": "Any liquid NSE stock at oversold extremes"
    },
    "Market Condition Scanner": {
        "icon": "🎛️", "type": "OB / OS / Fair Value + S/R Zones", "hold": "Informational",
        "accuracy": "Very High (6-indicator consensus)", "best_for": "Any ticker — pre-trade check"
    },
}

SIGNAL_BADGE = {
    "🔥 STRONG BUY": ("🔥", "#00cc66", "#003311"),
    "✅ BUY":        ("✅", "#33bb77", "#002211"),
    "⚠️ WATCH":     ("⚠️", "#ffaa00", "#332200"),
    "❌ AVOID":      ("❌", "#ff4444", "#330011"),
}

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")

    selected_strategies = st.multiselect(
        "🎯 Select Strategies",
        list(STRATEGIES.keys()),
        default=["RSI + MACD Combo"],
        help="Choose one or more strategies to run on every ticker"
    )

    if not selected_strategies:
        st.warning("Please select at least one strategy.")

    st.markdown("---")

    # Show info for each selected strategy
    for sname in selected_strategies:
        info = STRATEGY_INFO.get(sname, {})
        if info:
            st.markdown(f"**{info['icon']} {sname}**")
            st.caption(f"Type: {info['type']} | Hold: {info['hold']}")
            st.caption(f"Best for: {info['best_for']}")
            st.markdown("")

    st.markdown("---")
    st.markdown("### 🎚️ Score Thresholds")
    strong_buy_threshold = st.slider("🔥 Strong Buy (≥)", 60, 95, 80)
    buy_threshold        = st.slider("✅ Buy (≥)",        40, 79, 60)
    watch_threshold      = st.slider("⚠️ Watch (≥)",      20, 59, 40)
    alert_threshold      = st.slider("🔔 Send Alert (≥)", 50, 95, 70)

    st.markdown("---")
    enable_ai     = st.toggle("🤖 Enable AI Filter",        value=True)
    enable_alerts = st.toggle("📲 Enable Telegram Alerts",  value=True)

# ─── Main ────────────────────────────────────────────────────────────────────
st.title("📊 AI Swing Trading Dashboard — NSE/BSE")
st.caption(f"Running **{len(selected_strategies)}** strateg{'y' if len(selected_strategies)==1 else 'ies'} across all tickers")

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
scan_btn  = col1.button("🔍 Scan Market",   use_container_width=True)
show_logs = col2.button("📜 Trade History",  use_container_width=True)
clear_btn = col3.button("🗑️ Clear Results", use_container_width=True)

st.markdown("---")

# ─── Helper: classify score ───────────────────────────────────────────────────
def classify(score, strong_buy_threshold, buy_threshold, watch_threshold):
    if score >= strong_buy_threshold:
        return "🔥 STRONG BUY"
    elif score >= buy_threshold:
        return "✅ BUY"
    elif score >= watch_threshold:
        return "⚠️ WATCH"
    else:
        return "❌ AVOID"


def render_signal_badge(category):
    icon, border, bg = SIGNAL_BADGE.get(category, ("❓", "#888", "#111"))
    return (
        f'<span style="background:{bg};border:1.5px solid {border};'
        f'color:{border};border-radius:6px;padding:3px 10px;font-weight:bold;font-size:0.9em">'
        f'{category}</span>'
    )


# ─── SCAN ────────────────────────────────────────────────────────────────────
if scan_btn:
    if not selected_strategies:
        st.error("Please select at least one strategy from the sidebar.")
        st.stop()

    if not symbols:
        st.error("Please enter at least one symbol.")
        st.stop()

    all_results = []       # flat list of every (symbol, strategy, result)
    errors      = []       # list of (symbol, strategy, reason)

    total_tasks = len(symbols) * len(selected_strategies)
    progress    = st.progress(0, text="Starting scan…")
    task_idx    = 0

    # ── Per-symbol tabs ─────────────────────────────────────────────────────
    symbol_tabs = st.tabs([f"📌 {sym}" for sym in symbols])

    for tab, symbol in zip(symbol_tabs, symbols):
        with tab:
            st.subheader(f"📊 {symbol}")

            # Fetch data ONCE per symbol (reused for all strategies)
            df_daily = None
            df_ltf   = None
            data_error = None

            try:
                df_daily = fetch_ohlc(symbol, "day",       220)
                df_ltf   = fetch_ohlc(symbol, timeframe,   220)
            except Exception as e:
                data_error = str(e)

            if data_error or df_daily is None or df_ltf is None:
                reason = data_error or "No data returned"
                st.error(f"❌ **{symbol}**: Data fetch failed — {reason}")
                for strat in selected_strategies:
                    task_idx += 1
                    errors.append({"Symbol": symbol, "Strategy": strat, "Reason": reason})
                    progress.progress(task_idx / total_tasks, text=f"Data error: {symbol}")
                continue

            st.caption(
                f"✅ Daily: **{len(df_daily)}** candles | "
                f"{timeframe}: **{len(df_ltf)}** candles"
            )

            symbol_results = []   # results for this symbol across strategies

            # ── Run each strategy ────────────────────────────────────────────
            for strategy_name in selected_strategies:
                task_idx += 1
                progress.progress(
                    task_idx / total_tasks,
                    text=f"📡 {symbol} — {strategy_name}"
                )

                try:
                    trade = analyze_symbol(df_daily, df_ltf, strategy_name=strategy_name)
                except Exception as e:
                    errors.append({
                        "Symbol": symbol,
                        "Strategy": strategy_name,
                        "Reason": f"Strategy error: {traceback.format_exc(limit=2)}"
                    })
                    st.warning(f"⚠️ {strategy_name}: Strategy threw an error — skipped")
                    continue

                if trade is None:
                    st.caption(f"⬜ **{strategy_name}**: No signal / criteria not met")
                    continue

                # ── AI Filter ────────────────────────────────────────────────
                ai_score = 50
                ai_raw   = "AI filter disabled"
                try:
                    if enable_ai:
                        ai = analyze_trade(symbol, trade)
                        ai_score = ai["ai_score"]
                        ai_raw   = ai["raw"]
                        final_score = int(trade["strategy_score"] * 0.4 + ai_score * 0.6)
                    else:
                        final_score = trade["strategy_score"]
                except Exception as e:
                    ai_raw      = f"AI error: {e}"
                    final_score = trade["strategy_score"]

                category = classify(final_score, strong_buy_threshold, buy_threshold, watch_threshold)

                entry  = trade.get("Entry",  0)
                sl     = trade.get("SL",     0)
                target = trade.get("Target", 0)
                rr     = round((target - entry) / max(entry - sl, 0.01), 2)

                # Nearest S/R from trade dict (if present, else empty)
                nearest_supports    = trade.get("nearest_supports",    [])
                nearest_resistances = trade.get("nearest_resistances", [])

                # Derive support/resistance from key levels if not present
                if not nearest_supports and sl:
                    nearest_supports    = [{"level": sl,     "label": "SL (ATR-based)", "strength": 60}]
                if not nearest_resistances and target:
                    nearest_resistances = [{"level": target, "label": "Target (ATR-based)", "strength": 60}]

                row = {
                    "Symbol":            symbol,
                    "Strategy":          strategy_name,
                    "Entry":             entry,
                    "SL":                sl,
                    "Target":            target,
                    "R:R":               f"1:{rr}",
                    "Support":           ", ".join(f"₹{s['level']:.2f}" for s in nearest_supports[:2]) or "—",
                    "Resistance":        ", ".join(f"₹{r['level']:.2f}" for r in nearest_resistances[:2]) or "—",
                    "Strategy Score":    trade["strategy_score"],
                    "AI Score":          ai_score,
                    "Final Score":       final_score,
                    "Category":          category,
                    "AI Reason":         ai_raw,
                    "signals":           trade.get("signals", []),
                    # scanner extras
                    "condition":                trade.get("condition", ""),
                    "cond_score":               trade.get("cond_score", ""),
                    "action":                   trade.get("action", ""),
                    "nearest_supports_raw":     nearest_supports,
                    "nearest_resistances_raw":  nearest_resistances,
                    "key_levels":               trade.get("key_levels", {}),
                }

                symbol_results.append(row)
                all_results.append(row)

                # ── Telegram alert ───────────────────────────────────────────
                if enable_alerts and final_score >= alert_threshold:
                    try:
                        if strategy_name == "Market Condition Scanner":
                            sups_txt = "\n".join(
                                f"  S{j+1}: ₹{s['level']:.2f}"
                                for j, s in enumerate(nearest_supports)
                            ) or "  N/A"
                            res_txt = "\n".join(
                                f"  R{j+1}: ₹{r['level']:.2f}"
                                for j, r in enumerate(nearest_resistances)
                            ) or "  N/A"
                            msg = (
                                f"🎛️ MARKET SCAN [{symbol}]\n"
                                f"Condition: {trade.get('condition','')} (Score: {trade.get('cond_score',''):+})\n"
                                f"Action: {trade.get('action','')}\n"
                                f"CMP: ₹{entry}\n"
                                f"Supports:\n{sups_txt}\nResistances:\n{res_txt}\n"
                                f"SL: ₹{sl} | Target: ₹{target} | R:R 1:{rr}"
                            )
                        else:
                            msg = (
                                f"🚀 TRADE ALERT [{strategy_name}]\n"
                                f"Symbol: {symbol}\nScore: {final_score}/100 {category}\n"
                                f"Entry: ₹{entry}\nSL: ₹{sl}\nTarget: ₹{target}\nR:R: 1:{rr}"
                            )
                        ok, err = send_alert(msg)
                        if ok:
                            st.toast(f"📲 Alert sent: {symbol} [{strategy_name}]")
                        else:
                            st.warning(f"Telegram failed: {symbol} — {err}")
                        log_trade({k: v for k, v in row.items()
                                   if k not in ("signals","nearest_supports_raw","nearest_resistances_raw","key_levels")})
                    except Exception as e:
                        st.warning(f"Alert error for {symbol}: {e}")

            # ── Strategy Results Table for this symbol ───────────────────────
            if symbol_results:
                st.markdown("#### 📋 Strategy Signals")

                display_cols = ["Strategy", "Entry", "SL", "Target", "R:R",
                                "Support", "Resistance", "Strategy Score", "AI Score",
                                "Final Score", "Category"]
                df_sym = pd.DataFrame(symbol_results)[display_cols]
                df_sym = df_sym.sort_values("Final Score", ascending=False)

                # Color-coded Category column via styling
                def style_category(val):
                    _, border, bg = SIGNAL_BADGE.get(val, ("", "#888", "#222"))
                    return f"background-color: {bg}; color: {border}; font-weight: bold"

                styled = df_sym.style.applymap(style_category, subset=["Category"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

                # ── Per-strategy expanders with full signal log ──────────────
                st.markdown("#### 🔍 Strategy Detail Breakdown")
                for row in sorted(symbol_results, key=lambda x: x["Final Score"], reverse=True):
                    sname    = row["Strategy"]
                    cat      = row["Category"]
                    fscore   = row["Final Score"]
                    _, border, bg = SIGNAL_BADGE.get(cat, ("", "#888", "#222"))

                    with st.expander(
                        f"{STRATEGY_INFO.get(sname,{}).get('icon','📊')} "
                        f"{sname}  —  Score: {fscore}/100  {cat}",
                        expanded=(fscore >= buy_threshold)
                    ):
                        # Trade setup metrics
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("Entry",  f"₹{row['Entry']:.2f}")
                        m2.metric("Stop Loss", f"₹{row['SL']:.2f}",
                                  delta=f"-{((row['Entry']-row['SL'])/row['Entry']*100):.1f}%",
                                  delta_color="inverse")
                        m3.metric("Target", f"₹{row['Target']:.2f}",
                                  delta=f"+{((row['Target']-row['Entry'])/row['Entry']*100):.1f}%")
                        m4.metric("R:R",    row["R:R"])
                        m5.metric("Final Score", f"{fscore}/100")

                        st.markdown("")

                        # Support / Resistance zones
                        sr1, sr2 = st.columns(2)
                        with sr1:
                            st.markdown("**🟢 Support Zones**")
                            for j, s in enumerate(row["nearest_supports_raw"][:3], 1):
                                dist = (row["Entry"] - s["level"]) / row["Entry"] * 100
                                bar  = "█" * (s.get("strength", 50) // 20)
                                st.markdown(
                                    f'<div style="background:#00cc6622;border-left:3px solid #00cc66;'
                                    f'padding:6px 10px;margin:3px 0;border-radius:4px;">'
                                    f'S{j}: <b>₹{s["level"]:.2f}</b> &nbsp;·&nbsp; '
                                    f'{dist:.1f}% below &nbsp;·&nbsp; {bar} {s.get("strength",50)}%'
                                    f'{"&nbsp;·&nbsp; <i>"+s.get("label","")+"</i>" if s.get("label") else ""}'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )

                        with sr2:
                            st.markdown("**🔴 Resistance Zones**")
                            for j, r in enumerate(row["nearest_resistances_raw"][:3], 1):
                                dist = (r["level"] - row["Entry"]) / row["Entry"] * 100
                                bar  = "█" * (r.get("strength", 50) // 20)
                                st.markdown(
                                    f'<div style="background:#ff444422;border-left:3px solid #ff4444;'
                                    f'padding:6px 10px;margin:3px 0;border-radius:4px;">'
                                    f'R{j}: <b>₹{r["level"]:.2f}</b> &nbsp;·&nbsp; '
                                    f'{dist:.1f}% above &nbsp;·&nbsp; {bar} {r.get("strength",50)}%'
                                    f'{"&nbsp;·&nbsp; <i>"+r.get("label","")+"</i>" if r.get("label") else ""}'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )

                        # Market Condition Scanner extra info
                        if sname == "Market Condition Scanner" and row.get("condition"):
                            st.markdown("---")
                            cond_color_map = {
                                "🔴": "#ff4444", "🟠": "#ff8800",
                                "🟢": "#00cc66", "🔵": "#3399ff", "💜": "#9966ff"
                            }
                            badge_color = next(
                                (v for k, v in cond_color_map.items() if k in row["condition"]), "#888"
                            )
                            cc1, cc2, cc3 = st.columns([2, 1, 3])
                            with cc1:
                                st.markdown(
                                    f'<div style="background:{badge_color}22;border:2px solid {badge_color};'
                                    f'border-radius:8px;padding:10px;text-align:center;">'
                                    f'<b style="font-size:1.1em">{row["condition"]}</b></div>',
                                    unsafe_allow_html=True
                                )
                            with cc2:
                                st.metric("Cond Score", f'{row["cond_score"]:+}')
                            with cc3:
                                st.info(f'💡 {row.get("action","")}')

                            kl = row.get("key_levels", {})
                            if kl:
                                st.markdown("**📏 Key Levels**")
                                kl_items = [
                                    ("VWAP", kl.get("vwap"), "#ffcc00"),
                                    ("EMA20", kl.get("ema20"), "#ff8800"),
                                    ("EMA50", kl.get("ema50"), "#3399ff"),
                                    ("EMA200", kl.get("ema200"), "#cc44ff"),
                                    ("BB Upper", kl.get("bb_upper"), "#ff4444"),
                                    ("BB Lower", kl.get("bb_lower"), "#00cc66"),
                                    ("ATR(14)", kl.get("atr"), "#888888"),
                                ]
                                kl_cols = st.columns(4)
                                for idx, (lbl, val, color) in enumerate(kl_items):
                                    if val is not None:
                                        with kl_cols[idx % 4]:
                                            st.markdown(
                                                f'<div style="background:#1a1a2e;border:1px solid {color}44;'
                                                f'border-radius:6px;padding:6px;margin:2px;">'
                                                f'<span style="color:{color};font-size:0.72em">{lbl}</span><br>'
                                                f'<b>₹{val:.2f}</b></div>',
                                                unsafe_allow_html=True
                                            )

                        # Signal log
                        if row["signals"]:
                            st.markdown("---")
                            st.markdown("**📋 Full Signal Log**")
                            for sig in row["signals"]:
                                st.text(sig)

                        # AI Reason
                        if enable_ai:
                            st.markdown("---")
                            st.markdown("**🤖 AI Analysis**")
                            st.code(row["AI Reason"])

                # ── Candlestick chart for this symbol ────────────────────────
                st.markdown("#### 📈 Price Chart")
                try:
                    from strategy import ema as calc_ema, vwap as calc_vwap
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df_ltf.index,
                        open=df_ltf['Open'], high=df_ltf['High'],
                        low=df_ltf['Low'],  close=df_ltf['Close'],
                        name=symbol
                    ))
                    df_ltf['EMA20'] = calc_ema(df_ltf['Close'], 20)
                    df_ltf['EMA50'] = calc_ema(df_ltf['Close'], 50)
                    fig.add_trace(go.Scatter(
                        x=df_ltf.index, y=df_ltf['EMA20'],
                        line=dict(color='orange', width=1.5), name='EMA20'
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_ltf.index, y=df_ltf['EMA50'],
                        line=dict(color='royalblue', width=1.5), name='EMA50'
                    ))

                    # Draw all entry/SL/Target lines from every strategy
                    colors_entry  = ['#00cc66', '#33ff99', '#66ffaa', '#99ffcc']
                    colors_sl     = ['#ff4444', '#ff7777', '#ffaaaa', '#ffcccc']
                    colors_target = ['#ffcc00', '#ffdd44', '#ffee88', '#ffffaa']

                    for ridx, row in enumerate(symbol_results):
                        sn_short = row["Strategy"].split()[0]
                        ec = colors_entry[ridx  % len(colors_entry)]
                        sc = colors_sl[ridx     % len(colors_sl)]
                        tc = colors_target[ridx % len(colors_target)]
                        fig.add_hline(y=row["Entry"],  line_dash="dot",   line_color=ec,
                                      annotation_text=f"E ({sn_short})")
                        fig.add_hline(y=row["SL"],     line_dash="dash",  line_color=sc,
                                      annotation_text=f"SL ({sn_short})")
                        fig.add_hline(y=row["Target"], line_dash="longdash", line_color=tc,
                                      annotation_text=f"T ({sn_short})")

                        # Draw all S/R zones from Market Condition Scanner
                        if row["Strategy"] == "Market Condition Scanner":
                            df_ltf['VWAP'] = calc_vwap(df_ltf)
                            fig.add_trace(go.Scatter(
                                x=df_ltf.index, y=df_ltf['VWAP'],
                                line=dict(color='yellow', width=1.2, dash='dot'),
                                name='VWAP'
                            ))
                            for sup in row.get("nearest_supports_raw", []):
                                fig.add_hline(y=sup["level"],
                                    line_dash="dash", line_color="rgba(0,204,102,0.5)",
                                    annotation_text=f"S: ₹{sup['level']:.2f}",
                                    annotation_font_color="rgba(0,204,102,1)")
                            for res in row.get("nearest_resistances_raw", []):
                                fig.add_hline(y=res["level"],
                                    line_dash="dash", line_color="rgba(255,68,68,0.5)",
                                    annotation_text=f"R: ₹{res['level']:.2f}",
                                    annotation_font_color="rgba(255,68,68,1)")

                    fig.update_layout(
                        title=f"{symbol} — {timeframe} | {', '.join(s.split()[0] for s in selected_strategies)}",
                        xaxis_rangeslider_visible=False,
                        height=480,
                        legend=dict(orientation="h", y=1.05)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Chart error for {symbol}: {e}")

            else:
                st.info(f"ℹ️ {symbol}: No strategy produced a valid signal.")

    progress.progress(1.0, text="✅ Scan complete!")

    # ─── Summary Table (all symbols × strategies) ────────────────────────────
    if all_results:
        st.markdown("---")
        st.markdown("## 📊 Full Scan Summary")

        df_all = pd.DataFrame(all_results)
        df_all = df_all.sort_values(["Final Score", "Symbol"], ascending=[False, True])

        summary_cols = ["Symbol", "Strategy", "Entry", "SL", "Target", "R:R",
                        "Support", "Resistance", "Strategy Score", "AI Score",
                        "Final Score", "Category"]

        def style_row(row):
            _, border, bg = SIGNAL_BADGE.get(row["Category"], ("", "#888", "#222"))
            return [f"background-color: {bg}; color: {border}; font-weight: bold"
                    if col == "Category" else "" for col in summary_cols]

        styled_all = df_all[summary_cols].style.apply(style_row, axis=1)
        st.dataframe(styled_all, use_container_width=True, hide_index=True)

        # ── Aggregate stats ──────────────────────────────────────────────────
        st.markdown("### 📈 Scan Statistics")
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Total Signals",  len(df_all))
        mc2.metric("Strong Buys 🔥", len(df_all[df_all["Category"] == "🔥 STRONG BUY"]))
        mc3.metric("Buys ✅",        len(df_all[df_all["Category"] == "✅ BUY"]))
        mc4.metric("Avg Score",      f"{df_all['Final Score'].mean():.1f}")
        mc5.metric("Symbols Scanned", len(symbols))

    # ── Error report ─────────────────────────────────────────────────────────
    if errors:
        with st.expander(f"⚠️ {len(errors)} Error(s) during scan"):
            st.dataframe(pd.DataFrame(errors), use_container_width=True)

# ─── HISTORY ─────────────────────────────────────────────────────────────────
if show_logs:
    trades = load_trades()
    if not trades.empty:
        st.subheader("📜 Trade History")
        if "Strategy" in trades.columns:
            strategy_filter = st.multiselect(
                "Filter by Strategy",
                options=trades["Strategy"].unique().tolist(),
                default=trades["Strategy"].unique().tolist()
            )
            trades = trades[trades["Strategy"].isin(strategy_filter)]

        st.dataframe(trades, use_container_width=True)

        if "Final Score" in trades.columns:
            ca, cb, cc = st.columns(3)
            ca.metric("Total Alerts",  len(trades))
            cb.metric("Avg Score",     f"{trades['Final Score'].mean():.1f}")
            cc.metric("Strong Buys",   len(trades[trades["Final Score"] >= 80]))
    else:
        st.info("No trades logged yet.")