"""
strategy.py — Multi-Strategy Swing Trading Engine for Indian Markets (NSE/BSE)

Strategies available:
  1. RSI + MACD Combo           — Momentum confirmation
  2. EMA Crossover              — Trend following
  3. Support & Resistance Breakout — Volume-confirmed breakouts
  4. Fibonacci Retracement      — Pullback entries
  5. RSI Divergence             — Counter-trend RSI reversals
  6. Bollinger Band Squeeze     — Volatility breakout
  7. Supertrend + VWAP          — Trend + institutional price confluence
  8. Price & Volume Divergence  — Smart money divergence (price vs volume)
  9. Price & RSI Divergence     — Classic momentum divergence (enhanced)
 10. Market Condition Scanner   — Overbought/Oversold/Fair Value + nearest S/R zones
"""

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────
#  INDICATOR LIBRARY
# ─────────────────────────────────────────────

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def sma(series, period):
    return series.rolling(period).mean()


def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))


def macd(df, fast=12, slow=26, signal=9):
    fast_ema = ema(df['Close'], fast)
    slow_ema = ema(df['Close'], slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(df, period=20, std_dev=2):
    mid = sma(df['Close'], period)
    std = df['Close'].rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    bandwidth = (upper - lower) / (mid + 1e-10)
    return upper, mid, lower, bandwidth


def atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def swing_high_low(df, lookback=30):
    high = df['High'].rolling(lookback).max().iloc[-1]
    low  = df['Low'].rolling(lookback).min().iloc[-1]
    return high, low


def volume_ratio(df, period=20):
    avg_vol = df['Volume'].rolling(period).mean().iloc[-1]
    curr_vol = df['Volume'].iloc[-1]
    return curr_vol / (avg_vol + 1e-10)


def detect_rsi_divergence(df_ltf, rsi_series, lookback=5):
    """
    Returns ('bullish', strength) | ('bearish', strength) | (None, 0)
    Compares last two swing lows/highs in price vs RSI.
    """
    prices = df_ltf['Close'].values
    rsi_vals = rsi_series.values

    if len(prices) < lookback * 2:
        return None, 0

    prev_price = prices[-(lookback + 1)]
    curr_price = prices[-1]
    prev_rsi   = rsi_vals[-(lookback + 1)]
    curr_rsi   = rsi_vals[-1]

    # Bullish divergence: price makes lower low, RSI makes higher low
    if curr_price < prev_price and curr_rsi > prev_rsi and curr_rsi < 45:
        strength = min(int((curr_rsi - prev_rsi) * 2), 30)
        return 'bullish', strength

    # Bearish divergence: price makes higher high, RSI makes lower high
    if curr_price > prev_price and curr_rsi < prev_rsi and curr_rsi > 55:
        strength = min(int((prev_rsi - curr_rsi) * 2), 30)
        return 'bearish', strength

    return None, 0


# ─────────────────────────────────────────────
#  STRATEGY 1 — RSI + MACD COMBO
# ─────────────────────────────────────────────

def strategy_rsi_macd(df_htf, df_ltf):
    """
    Entry: RSI near oversold (30-45) + MACD bullish crossover on LTF.
    Trend filter: Price above EMA50 on HTF.
    Exit: RSI reaches 60-70 OR MACD histogram turns negative.
    """
    signals = []
    score = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # HTF Trend filter
    df_htf['EMA50'] = ema(df_htf['Close'], 50)
    df_htf['EMA200'] = ema(df_htf['Close'], 200)
    htf_latest = df_htf.iloc[-1]

    if htf_latest['Close'] > htf_latest['EMA50']:
        score += 15
        signals.append("✅ HTF: Price above EMA50 — Uptrend confirmed")
    else:
        signals.append("❌ HTF: Price below EMA50 — Downtrend")

    if htf_latest['EMA50'] > htf_latest['EMA200']:
        score += 10
        signals.append("✅ HTF: EMA50 > EMA200 — Bull market structure")
    else:
        signals.append("⚠️ HTF: EMA50 < EMA200 — Bearish structure")

    # LTF RSI
    df_ltf['RSI'] = rsi(df_ltf)
    rsi_val = df_ltf['RSI'].iloc[-1]
    rsi_prev = df_ltf['RSI'].iloc[-2]

    if 30 <= rsi_val <= 45:
        score += 25
        signals.append(f"✅ RSI Oversold zone ({rsi_val:.1f}) — Strong buy signal")
    elif 45 < rsi_val <= 55:
        score += 15
        signals.append(f"✅ RSI Neutral ({rsi_val:.1f}) — Acceptable entry")
    elif rsi_val < 30:
        score += 10
        signals.append(f"⚠️ RSI Extremely oversold ({rsi_val:.1f}) — Wait for bounce confirmation")
    else:
        signals.append(f"❌ RSI High ({rsi_val:.1f}) — Avoid chasing")

    # RSI turning up
    if rsi_val > rsi_prev and rsi_val < 55:
        score += 10
        signals.append(f"✅ RSI trending up ({rsi_prev:.1f} → {rsi_val:.1f})")

    # LTF MACD
    macd_line, signal_line, histogram = macd(df_ltf)
    curr_hist = histogram.iloc[-1]
    prev_hist = histogram.iloc[-2]
    curr_macd = macd_line.iloc[-1]
    curr_sig  = signal_line.iloc[-1]

    # Bullish crossover: MACD crossed above signal
    if curr_macd > curr_sig and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        score += 25
        signals.append(f"✅ MACD Bullish crossover — Strong momentum signal")
    elif curr_macd > curr_sig:
        score += 15
        signals.append(f"✅ MACD above signal line — Momentum positive")
    elif curr_hist > prev_hist:
        score += 8
        signals.append(f"✅ MACD histogram improving — Momentum building")
    else:
        signals.append(f"❌ MACD bearish — No momentum confirmation")

    # Volume confirmation
    vol_r = volume_ratio(df_ltf)
    if vol_r >= 1.5:
        score += 15
        signals.append(f"✅ Volume surge {vol_r:.1f}x avg — Institutional interest")
    elif vol_r >= 1.0:
        score += 5
        signals.append(f"✅ Volume normal {vol_r:.1f}x avg")
    else:
        signals.append(f"⚠️ Volume low {vol_r:.1f}x avg — Weak participation")

    price = df_ltf['Close'].iloc[-1]
    atr_val = atr(df_ltf).iloc[-1]
    swing_high, swing_low = swing_high_low(df_htf)

    sl = round(price - 1.5 * atr_val, 2)
    target = round(price + 3.0 * atr_val, 2)
    rr = round((target - price) / (price - sl), 2) if price > sl else 0

    signals.append(f"📐 Risk:Reward = 1:{rr} | ATR = {atr_val:.2f}")

    if score >= 20:
        return {
            "Entry": round(price, 2),
            "SL": sl,
            "Target": target,
            "strategy_score": min(score, 100),
            "signals": signals,
            "strategy_name": "RSI + MACD Combo"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 2 — EMA CROSSOVER (TREND FOLLOWING)
# ─────────────────────────────────────────────

def strategy_ema_crossover(df_htf, df_ltf):
    """
    Entry: 20 EMA crosses above 50 EMA on LTF, confirmed by HTF trend.
    Exit: Price closes below 20 EMA OR 20 EMA crosses back below 50 EMA.
    """
    signals = []
    score = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # HTF structure
    df_htf['EMA50'] = ema(df_htf['Close'], 50)
    df_htf['EMA200'] = ema(df_htf['Close'], 200)
    htf_latest = df_htf.iloc[-1]

    htf_bullish = htf_latest['Close'] > htf_latest['EMA50']
    if htf_bullish:
        score += 20
        signals.append("✅ HTF: Bullish — Price above EMA50")
    else:
        signals.append("❌ HTF: Bearish — Price below EMA50")

    if htf_latest['EMA50'] > htf_latest['EMA200']:
        score += 10
        signals.append("✅ HTF: Golden cross structure (EMA50 > EMA200)")

    # LTF EMA crossover signals
    df_ltf['EMA9']  = ema(df_ltf['Close'], 9)
    df_ltf['EMA20'] = ema(df_ltf['Close'], 20)
    df_ltf['EMA50'] = ema(df_ltf['Close'], 50)

    curr = df_ltf.iloc[-1]
    prev = df_ltf.iloc[-2]

    # 20 EMA freshly crosses above 50 EMA
    golden_cross_now = curr['EMA20'] > curr['EMA50'] and prev['EMA20'] <= prev['EMA50']
    golden_cross_recent = curr['EMA20'] > curr['EMA50']

    if golden_cross_now:
        score += 35
        signals.append("✅ LTF: FRESH EMA20 × EMA50 Golden Cross — Prime entry!")
    elif golden_cross_recent:
        score += 20
        signals.append("✅ LTF: EMA20 above EMA50 — Uptrend active")
    else:
        signals.append("❌ LTF: EMA20 below EMA50 — No bullish crossover")

    # 9 EMA as fast momentum check
    if curr['Close'] > curr['EMA9'] > curr['EMA20'] > curr['EMA50']:
        score += 20
        signals.append("✅ LTF: Perfect EMA stack (Price > EMA9 > EMA20 > EMA50)")
    elif curr['Close'] > curr['EMA20']:
        score += 10
        signals.append("✅ LTF: Price above EMA20")

    # EMA slope (momentum)
    ema20_slope = (curr['EMA20'] - df_ltf['EMA20'].iloc[-5]) / df_ltf['EMA20'].iloc[-5] * 100
    if ema20_slope > 0.3:
        score += 15
        signals.append(f"✅ EMA20 rising sharply (+{ema20_slope:.2f}%) — Strong momentum")
    elif ema20_slope > 0:
        score += 8
        signals.append(f"✅ EMA20 rising ({ema20_slope:.2f}%)")
    else:
        signals.append(f"❌ EMA20 declining ({ema20_slope:.2f}%)")

    # Volume
    vol_r = volume_ratio(df_ltf)
    if vol_r >= 1.5:
        score += 15
        signals.append(f"✅ Volume {vol_r:.1f}x avg — Strong participation")
    elif vol_r >= 1.0:
        score += 5
        signals.append(f"✅ Volume {vol_r:.1f}x avg")

    price = df_ltf['Close'].iloc[-1]
    atr_val = atr(df_ltf).iloc[-1]

    sl = round(curr['EMA50'] - 0.5 * atr_val, 2)
    target = round(price + 2.5 * atr_val, 2)
    rr = round((target - price) / max(price - sl, 0.01), 2)

    signals.append(f"📐 Risk:Reward = 1:{rr} | EMA50 SL: {sl}")

    if score >= 25:
        return {
            "Entry": round(price, 2),
            "SL": sl,
            "Target": target,
            "strategy_score": min(score, 100),
            "signals": signals,
            "strategy_name": "EMA Crossover"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 3 — SUPPORT & RESISTANCE BREAKOUT
# ─────────────────────────────────────────────

def strategy_sr_breakout(df_htf, df_ltf):
    """
    Entry: Price breaks above key resistance with volume surge (1.5x+).
    SL: Below the breakout candle's low.
    Exit: At next major resistance level OR trailing stop.
    """
    signals = []
    score = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # Find resistance: recent swing high in HTF
    resistance = df_htf['High'].rolling(20).max().shift(1).iloc[-1]
    support    = df_htf['Low'].rolling(20).min().shift(1).iloc[-1]

    price = df_ltf['Close'].iloc[-1]
    prev_close = df_ltf['Close'].iloc[-2]

    # Breakout detection
    broke_resistance = prev_close <= resistance and price > resistance
    extended_breakout = price > resistance and (price - resistance) / resistance < 0.03  # within 3%

    if broke_resistance:
        score += 40
        signals.append(f"✅ FRESH Resistance Breakout at ₹{resistance:.2f} — High priority!")
    elif extended_breakout:
        score += 20
        signals.append(f"✅ Recent breakout — within 3% of resistance ₹{resistance:.2f}")
    else:
        gap_pct = (resistance - price) / price * 100
        signals.append(f"❌ Price {gap_pct:.1f}% below resistance ₹{resistance:.2f}")

    # Volume confirmation — critical for breakouts
    vol_r = volume_ratio(df_ltf)
    if vol_r >= 2.0:
        score += 25
        signals.append(f"✅ Massive volume surge {vol_r:.1f}x avg — Institutional breakout!")
    elif vol_r >= 1.5:
        score += 18
        signals.append(f"✅ Strong volume {vol_r:.1f}x avg — Confirmed breakout")
    elif vol_r >= 1.2:
        score += 8
        signals.append(f"⚠️ Moderate volume {vol_r:.1f}x avg — Weak confirmation")
    else:
        signals.append(f"❌ Low volume {vol_r:.1f}x avg — Likely false breakout")

    # Trend context
    df_htf['EMA50'] = ema(df_htf['Close'], 50)
    if df_htf['Close'].iloc[-1] > df_htf['EMA50'].iloc[-1]:
        score += 15
        signals.append("✅ HTF uptrend supports breakout")
    else:
        signals.append("⚠️ HTF downtrend — breakout against trend (risky)")

    # Consolidation before breakout (tight range = good)
    recent_range = (df_ltf['High'].iloc[-5:].max() - df_ltf['Low'].iloc[-5:].min()) / price
    if recent_range < 0.03:
        score += 15
        signals.append(f"✅ Tight consolidation ({recent_range*100:.1f}%) before breakout")
    elif recent_range < 0.06:
        score += 8
        signals.append(f"✅ Normal consolidation ({recent_range*100:.1f}%)")
    else:
        signals.append(f"⚠️ Wide range ({recent_range*100:.1f}%) — volatile base")

    # RSI check — not overbought
    df_ltf['RSI'] = rsi(df_ltf)
    rsi_val = df_ltf['RSI'].iloc[-1]
    if 50 <= rsi_val <= 70:
        score += 10
        signals.append(f"✅ RSI {rsi_val:.1f} — Momentum healthy")
    elif rsi_val > 70:
        signals.append(f"⚠️ RSI overbought ({rsi_val:.1f}) — Wait for pullback")
    else:
        signals.append(f"⚠️ RSI weak ({rsi_val:.1f})")

    atr_val = atr(df_ltf).iloc[-1]
    breakout_candle_low = df_ltf['Low'].iloc[-1]
    sl = round(breakout_candle_low - 0.3 * atr_val, 2)

    # Next resistance as target
    next_resistance = df_htf['High'].rolling(60).max().iloc[-1]
    target = round(max(next_resistance, price + 3 * atr_val), 2)
    rr = round((target - price) / max(price - sl, 0.01), 2)

    signals.append(f"📐 Breakout level: ₹{resistance:.2f} | Risk:Reward = 1:{rr}")

    if score >= 35:
        return {
            "Entry": round(price, 2),
            "SL": sl,
            "Target": target,
            "strategy_score": min(score, 100),
            "signals": signals,
            "strategy_name": "S&R Breakout"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 4 — FIBONACCI RETRACEMENT (UPGRADED)
# ─────────────────────────────────────────────

def strategy_fibonacci(df_htf, df_ltf):
    """
    Entry: Price pulls back to 38.2%, 50%, or 61.8% Fibonacci level in uptrend.
    Confirmation: RSI not oversold, volume declining on pullback (healthy).
    Exit: Previous high (100% Fib extension) or 127.2%/161.8% extension.
    """
    signals = []
    score = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # Trend filter — must be in uptrend
    df_htf['EMA50'] = ema(df_htf['Close'], 50)
    htf_latest = df_htf.iloc[-1]

    uptrend = htf_latest['Close'] > htf_latest['EMA50']
    if uptrend:
        score += 20
        signals.append("✅ HTF Uptrend — Fibonacci pullback is valid")
    else:
        signals.append("❌ HTF Downtrend — Fibonacci entry is counter-trend (risky)")

    # Identify the last significant swing (over 30 candles)
    swing_high, swing_low = swing_high_low(df_htf, lookback=30)
    swing_size = swing_high - swing_low

    # Fibonacci levels
    fib_236 = swing_high - 0.236 * swing_size
    fib_382 = swing_high - 0.382 * swing_size
    fib_500 = swing_high - 0.500 * swing_size
    fib_618 = swing_high - 0.618 * swing_size
    fib_786 = swing_high - 0.786 * swing_size

    price = df_ltf['Close'].iloc[-1]
    tolerance = swing_size * 0.03  # 3% tolerance band

    # Check which Fibonacci zone price is in
    if abs(price - fib_382) <= tolerance:
        score += 30
        signals.append(f"✅ At 38.2% Fib (₹{fib_382:.2f}) — Shallow pullback, strong trend")
    elif abs(price - fib_500) <= tolerance:
        score += 35
        signals.append(f"✅ At 50% Fib (₹{fib_500:.2f}) — Classic swing entry zone")
    elif abs(price - fib_618) <= tolerance:
        score += 40
        signals.append(f"✅ At 61.8% Golden Ratio (₹{fib_618:.2f}) — PRIME entry zone!")
    elif abs(price - fib_786) <= tolerance:
        score += 20
        signals.append(f"✅ At 78.6% Fib (₹{fib_786:.2f}) — Deep pullback, risky")
    elif price > fib_236:
        signals.append(f"❌ Price too high (above 23.6% Fib) — No pullback yet")
    else:
        signals.append(f"❌ Price too low (below 78.6% Fib) — Trend may be broken")

    # RSI confirmation — should be recovering but not overbought
    df_ltf['RSI'] = rsi(df_ltf)
    rsi_val = df_ltf['RSI'].iloc[-1]
    rsi_prev = df_ltf['RSI'].iloc[-3]

    if 35 <= rsi_val <= 55 and rsi_val > rsi_prev:
        score += 20
        signals.append(f"✅ RSI recovering ({rsi_prev:.1f} → {rsi_val:.1f}) — Momentum returning")
    elif 35 <= rsi_val <= 55:
        score += 12
        signals.append(f"✅ RSI neutral ({rsi_val:.1f}) — OK entry")
    elif rsi_val < 35:
        score += 5
        signals.append(f"⚠️ RSI weak ({rsi_val:.1f}) — Wait for bounce")
    else:
        signals.append(f"❌ RSI elevated ({rsi_val:.1f}) — Not a pullback")

    # Volume declining during pullback (healthy retracement)
    vol_recent  = df_ltf['Volume'].iloc[-3:].mean()
    vol_earlier = df_ltf['Volume'].iloc[-8:-3].mean()
    if vol_recent < vol_earlier * 0.8:
        score += 15
        signals.append("✅ Volume declining on pullback — Healthy retracement")
    elif vol_recent < vol_earlier:
        score += 8
        signals.append("✅ Volume tapering on pullback")
    else:
        signals.append("⚠️ Volume not declining — May not be a pullback")

    atr_val = atr(df_ltf).iloc[-1]
    sl = round(fib_786 - atr_val * 0.5, 2)  # below deepest valid fib
    target = round(swing_high + 0.272 * swing_size, 2)  # 127.2% extension
    rr = round((target - price) / max(price - sl, 0.01), 2)

    signals.append(f"📐 Swing: ₹{swing_low:.2f} → ₹{swing_high:.2f} | Target ext: ₹{target:.2f} | R:R = 1:{rr}")

    if score >= 35:
        return {
            "Entry": round(price, 2),
            "SL": sl,
            "Target": target,
            "strategy_score": min(score, 100),
            "signals": signals,
            "strategy_name": "Fibonacci Retracement"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 5 — RSI DIVERGENCE (REVERSAL)
# ─────────────────────────────────────────────

def strategy_rsi_divergence(df_htf, df_ltf):
    """
    Entry: Bullish RSI divergence (price lower low, RSI higher low) near support.
    Exit: When RSI reaches 65+ or price hits next resistance.
    Best for: Catching reversals at key support zones.
    """
    signals = []
    score = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    df_ltf['RSI'] = rsi(df_ltf)

    # Detect divergence
    div_type, div_strength = detect_rsi_divergence(df_ltf, df_ltf['RSI'], lookback=5)

    if div_type == 'bullish':
        score += 40 + div_strength
        signals.append(f"✅ BULLISH RSI Divergence detected (strength: {div_strength}) — Reversal signal!")
    elif div_type == 'bearish':
        score += 15
        signals.append(f"⚠️ Bearish divergence — Only valid for SHORT setups")
    else:
        signals.append("❌ No RSI divergence detected")

    # Support zone check
    swing_high, swing_low = swing_high_low(df_htf)
    price = df_ltf['Close'].iloc[-1]

    support_zone = swing_low * 1.05  # 5% above swing low
    if price <= support_zone:
        score += 20
        signals.append(f"✅ Price near support zone ₹{swing_low:.2f} — Divergence more reliable")
    else:
        signals.append(f"⚠️ Price not near key support (support: ₹{swing_low:.2f})")

    # RSI current level (divergence more powerful at extremes)
    rsi_val = df_ltf['RSI'].iloc[-1]
    if rsi_val < 30:
        score += 20
        signals.append(f"✅ RSI deeply oversold ({rsi_val:.1f}) — Strong reversal potential")
    elif rsi_val < 40:
        score += 12
        signals.append(f"✅ RSI oversold ({rsi_val:.1f}) — Reversal likely")
    else:
        signals.append(f"⚠️ RSI not oversold ({rsi_val:.1f}) — Divergence less reliable")

    # MACD histogram turning positive
    macd_line, signal_line, histogram = macd(df_ltf)
    if histogram.iloc[-1] > histogram.iloc[-2] and histogram.iloc[-2] > histogram.iloc[-3]:
        score += 15
        signals.append("✅ MACD histogram rising — Momentum confirming reversal")
    elif histogram.iloc[-1] > histogram.iloc[-2]:
        score += 8
        signals.append("✅ MACD histogram turning up")

    # HTF trend context
    df_htf['EMA200'] = ema(df_htf['Close'], 200)
    if df_htf['Close'].iloc[-1] > df_htf['EMA200'].iloc[-1]:
        score += 10
        signals.append("✅ HTF: Above EMA200 — Bullish long-term context")
    else:
        signals.append("⚠️ HTF: Below EMA200 — Countertrend trade")

    atr_val = atr(df_ltf).iloc[-1]
    sl = round(swing_low - 0.5 * atr_val, 2)
    target = round(price + 3.5 * atr_val, 2)
    rr = round((target - price) / max(price - sl, 0.01), 2)

    signals.append(f"📐 Divergence trade | Risk:Reward = 1:{rr} | SL below swing low: ₹{sl}")

    if score >= 40:
        return {
            "Entry": round(price, 2),
            "SL": sl,
            "Target": target,
            "strategy_score": min(score, 100),
            "signals": signals,
            "strategy_name": "RSI Divergence"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 6 — BOLLINGER BAND SQUEEZE
# ─────────────────────────────────────────────

def strategy_bollinger_squeeze(df_htf, df_ltf):
    """
    Entry: After a Bollinger Band squeeze (low bandwidth), trade the breakout
           in the direction of the trend when price closes outside the band.
    Exit: At upper band (for longs) or when price re-enters mid band.
    """
    signals = []
    score = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    upper, mid, lower, bandwidth = bollinger_bands(df_ltf)

    curr_bw   = bandwidth.iloc[-1]
    avg_bw    = bandwidth.rolling(50).mean().iloc[-1]
    min_bw_20 = bandwidth.rolling(20).min().iloc[-1]

    price = df_ltf['Close'].iloc[-1]

    # Squeeze detection: current bandwidth < 50% of average
    squeeze_ratio = curr_bw / (avg_bw + 1e-10)
    is_squeeze = curr_bw <= min_bw_20 * 1.1  # near recent minimum bandwidth

    if is_squeeze:
        score += 30
        signals.append(f"✅ ACTIVE SQUEEZE — Bandwidth {curr_bw:.3f} near 20-period low!")
    elif squeeze_ratio < 0.7:
        score += 20
        signals.append(f"✅ Low volatility — Bandwidth {squeeze_ratio:.0%} of average")
    elif squeeze_ratio < 0.9:
        score += 10
        signals.append(f"✅ Moderate compression — Bandwidth {squeeze_ratio:.0%} of average")
    else:
        signals.append(f"❌ No squeeze — Bandwidth normal ({squeeze_ratio:.0%} of avg)")

    # Breakout direction
    upper_val = upper.iloc[-1]
    lower_val = lower.iloc[-1]
    mid_val   = mid.iloc[-1]

    if price > upper_val:
        score += 30
        signals.append(f"✅ Price ABOVE upper band ₹{upper_val:.2f} — Bullish breakout!")
    elif price > mid_val and price < upper_val:
        score += 15
        signals.append(f"✅ Price above midband — Bullish bias, approaching upper band")
    elif price < lower_val:
        signals.append(f"❌ Price below lower band — Bearish breakout (not suitable for longs)")
    else:
        signals.append(f"⚠️ Price inside bands — Await breakout direction")

    # HTF trend alignment
    df_htf['EMA50'] = ema(df_htf['Close'], 50)
    if df_htf['Close'].iloc[-1] > df_htf['EMA50'].iloc[-1]:
        score += 15
        signals.append("✅ HTF uptrend — Bullish BB breakout favored")
    else:
        signals.append("⚠️ HTF downtrend — Caution on bullish breakout")

    # Momentum confirmation
    df_ltf['RSI'] = rsi(df_ltf)
    rsi_val = df_ltf['RSI'].iloc[-1]
    if 50 < rsi_val < 75:
        score += 15
        signals.append(f"✅ RSI {rsi_val:.1f} — Momentum supporting breakout")
    elif rsi_val >= 75:
        signals.append(f"⚠️ RSI overbought ({rsi_val:.1f}) — Breakout may be exhausted")
    else:
        signals.append(f"⚠️ RSI weak ({rsi_val:.1f}) — Breakout needs momentum")

    # Volume spike on breakout
    vol_r = volume_ratio(df_ltf)
    if vol_r >= 2.0:
        score += 20
        signals.append(f"✅ Volume explosion {vol_r:.1f}x — Confirmed breakout!")
    elif vol_r >= 1.5:
        score += 12
        signals.append(f"✅ Volume elevated {vol_r:.1f}x")
    else:
        signals.append(f"⚠️ Volume {vol_r:.1f}x — Needs stronger participation")

    atr_val = atr(df_ltf).iloc[-1]
    sl = round(mid_val - 0.3 * atr_val, 2)
    target = round(upper_val + 1.5 * (upper_val - mid_val), 2)
    rr = round((target - price) / max(price - sl, 0.01), 2)

    signals.append(f"📐 BB Upper: ₹{upper_val:.2f} | Mid: ₹{mid_val:.2f} | Risk:Reward = 1:{rr}")

    if score >= 35:
        return {
            "Entry": round(price, 2),
            "SL": sl,
            "Target": target,
            "strategy_score": min(score, 100),
            "signals": signals,
            "strategy_name": "Bollinger Band Squeeze"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 7 — SUPERTREND + VWAP
# ─────────────────────────────────────────────

def supertrend(df, period=10, multiplier=3.0):
    """
    Compute Supertrend indicator.
    Returns series: +1 = bullish (price above), -1 = bearish (price below).
    Also returns the supertrend line values.
    """
    atr_val = atr(df, period)
    hl_avg  = (df['High'] + df['Low']) / 2

    upper_band = hl_avg + multiplier * atr_val
    lower_band = hl_avg - multiplier * atr_val

    # Initialise
    supertrend_line = pd.Series(index=df.index, dtype=float)
    direction       = pd.Series(index=df.index, dtype=int)

    for i in range(1, len(df)):
        # Upper band
        if upper_band.iloc[i] < upper_band.iloc[i - 1] or df['Close'].iloc[i - 1] > upper_band.iloc[i - 1]:
            final_upper = upper_band.iloc[i]
        else:
            final_upper = upper_band.iloc[i - 1]

        # Lower band
        if lower_band.iloc[i] > lower_band.iloc[i - 1] or df['Close'].iloc[i - 1] < lower_band.iloc[i - 1]:
            final_lower = lower_band.iloc[i]
        else:
            final_lower = lower_band.iloc[i - 1]

        if df['Close'].iloc[i] > final_upper:
            direction.iloc[i]       = 1
            supertrend_line.iloc[i] = final_lower
        elif df['Close'].iloc[i] < final_lower:
            direction.iloc[i]       = -1
            supertrend_line.iloc[i] = final_upper
        else:
            direction.iloc[i]       = direction.iloc[i - 1] if i > 0 else 1
            supertrend_line.iloc[i] = (
                final_lower if direction.iloc[i] == 1 else final_upper
            )

    return direction, supertrend_line


def vwap(df):
    """
    Session VWAP — uses cumulative typical price × volume / cumulative volume.
    For swing trading we use a rolling 20-period approximation (no session reset).
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap_series   = (typical_price * df['Volume']).rolling(20).sum() / df['Volume'].rolling(20).sum()
    return vwap_series


def strategy_supertrend_vwap(df_htf, df_ltf):
    """
    Entry:  Supertrend bullish (price above Supertrend line) on BOTH HTF & LTF,
            AND price is above VWAP (institutional buy zone).
    Exit:   Price closes below Supertrend line OR below VWAP.
    Logic:  Supertrend = dynamic trend-following stop. VWAP = institutional fair value.
            Being above both = institutional momentum confirmed.
    """
    signals = []
    score   = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # ── HTF Supertrend ──────────────────────────────────────────────────────
    htf_dir, htf_st_line = supertrend(df_htf, period=10, multiplier=3.0)
    htf_dir_curr  = htf_dir.iloc[-1]
    htf_dir_prev  = htf_dir.iloc[-2]
    htf_st_val    = htf_st_line.iloc[-1]
    htf_price     = df_htf['Close'].iloc[-1]

    # Fresh bullish flip on HTF (highest value signal)
    if htf_dir_curr == 1 and htf_dir_prev == -1:
        score += 35
        signals.append(f"✅ HTF: FRESH Supertrend flip to BULLISH at ₹{htf_st_val:.2f} — Prime setup!")
    elif htf_dir_curr == 1:
        score += 20
        signals.append(f"✅ HTF: Supertrend BULLISH — support line ₹{htf_st_val:.2f}")
    else:
        score -= 10
        signals.append(f"❌ HTF: Supertrend BEARISH — price below ₹{htf_st_val:.2f}")

    # ── LTF Supertrend ──────────────────────────────────────────────────────
    ltf_dir, ltf_st_line = supertrend(df_ltf, period=7, multiplier=2.5)
    ltf_dir_curr = ltf_dir.iloc[-1]
    ltf_dir_prev = ltf_dir.iloc[-2]
    ltf_st_val   = ltf_st_line.iloc[-1]
    ltf_price    = df_ltf['Close'].iloc[-1]

    if ltf_dir_curr == 1 and ltf_dir_prev == -1:
        score += 30
        signals.append(f"✅ LTF: FRESH Supertrend flip BULLISH at ₹{ltf_st_val:.2f} — Entry trigger!")
    elif ltf_dir_curr == 1:
        score += 15
        signals.append(f"✅ LTF: Supertrend BULLISH — support ₹{ltf_st_val:.2f}")
    else:
        score += 0
        signals.append(f"❌ LTF: Supertrend BEARISH — no entry yet")

    # ── VWAP Analysis ───────────────────────────────────────────────────────
    ltf_vwap   = vwap(df_ltf)
    vwap_curr  = ltf_vwap.iloc[-1]
    vwap_prev  = ltf_vwap.iloc[-3]

    price_vs_vwap_pct = (ltf_price - vwap_curr) / vwap_curr * 100

    if ltf_price > vwap_curr:
        if price_vs_vwap_pct < 1.0:
            score += 25
            signals.append(f"✅ Price just above VWAP ₹{vwap_curr:.2f} (+{price_vs_vwap_pct:.2f}%) — Ideal entry zone")
        elif price_vs_vwap_pct < 3.0:
            score += 15
            signals.append(f"✅ Price above VWAP ₹{vwap_curr:.2f} (+{price_vs_vwap_pct:.2f}%) — Bullish")
        else:
            score += 5
            signals.append(f"⚠️ Price far above VWAP ({price_vs_vwap_pct:.2f}%) — Extended, wait for VWAP pullback")
    else:
        signals.append(f"❌ Price BELOW VWAP ₹{vwap_curr:.2f} ({price_vs_vwap_pct:.2f}%) — Institutional selling zone")

    # VWAP slope (institutional interest rising?)
    if vwap_curr > vwap_prev:
        score += 10
        signals.append(f"✅ VWAP rising — institutional accumulation ongoing")
    else:
        signals.append(f"⚠️ VWAP flat/falling — institutions not buying yet")

    # ── RSI confirmation ────────────────────────────────────────────────────
    df_ltf['RSI'] = rsi(df_ltf)
    rsi_val = df_ltf['RSI'].iloc[-1]
    if 45 < rsi_val < 70:
        score += 10
        signals.append(f"✅ RSI {rsi_val:.1f} — Momentum healthy, not overbought")
    elif rsi_val >= 70:
        signals.append(f"⚠️ RSI overbought ({rsi_val:.1f}) — Wait for pullback to VWAP")
    else:
        signals.append(f"⚠️ RSI weak ({rsi_val:.1f}) — Momentum not confirmed")

    # ── Volume ──────────────────────────────────────────────────────────────
    vol_r = volume_ratio(df_ltf)
    if vol_r >= 1.5:
        score += 10
        signals.append(f"✅ Volume {vol_r:.1f}x avg — Institutional participation")
    else:
        signals.append(f"⚠️ Volume {vol_r:.1f}x avg — Light volume")

    # ── Trade levels ────────────────────────────────────────────────────────
    atr_val = atr(df_ltf).iloc[-1]
    # SL = Supertrend line on LTF (dynamic trailing stop)
    sl      = round(ltf_st_val - 0.2 * atr_val, 2)
    target  = round(ltf_price + 3.0 * atr_val, 2)
    rr      = round((target - ltf_price) / max(ltf_price - sl, 0.01), 2)

    signals.append(f"📐 Supertrend SL: ₹{ltf_st_val:.2f} | VWAP: ₹{vwap_curr:.2f} | R:R = 1:{rr}")

    if score >= 40:
        return {
            "Entry":          round(ltf_price, 2),
            "SL":             sl,
            "Target":         target,
            "strategy_score": min(score, 100),
            "signals":        signals,
            "strategy_name":  "Supertrend + VWAP"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 8 — PRICE & VOLUME DIVERGENCE
# ─────────────────────────────────────────────

def obv(df):
    """On Balance Volume — cumulative volume following price direction."""
    direction = df['Close'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * df['Volume']).cumsum()


def strategy_price_volume_divergence(df_htf, df_ltf):
    """
    Price & Volume Divergence — Smart Money Detection.

    Bullish divergence: Price makes lower lows BUT volume on down candles
                        is DECREASING (sellers losing conviction).
                        OBV makes higher lows while price makes lower lows.

    Bearish divergence: Price makes higher highs BUT volume on up candles
                        is DECREASING (buyers losing conviction).
                        OBV makes lower highs while price makes higher highs.

    Entry: Bullish divergence at support + OBV turning up.
    Exit:  Price reaches next resistance or OBV diverges bearishly.
    """
    signals = []
    score   = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # ── OBV computation ─────────────────────────────────────────────────────
    df_ltf['OBV'] = obv(df_ltf)
    obv_series    = df_ltf['OBV']
    prices        = df_ltf['Close']
    volumes       = df_ltf['Volume']

    lookback = 10   # bars to look back for divergence comparison

    if len(df_ltf) < lookback * 2:
        signals.append("⚠️ Not enough data for divergence analysis")
        return None

    # Compare two windows: recent vs prior
    recent_prices  = prices.iloc[-lookback:].values
    prior_prices   = prices.iloc[-lookback * 2:-lookback].values
    recent_obv     = obv_series.iloc[-lookback:].values
    prior_obv      = obv_series.iloc[-lookback * 2:-lookback].values
    recent_volumes = volumes.iloc[-lookback:].values
    prior_volumes  = volumes.iloc[-lookback * 2:-lookback].values

    recent_price_low  = recent_prices.min()
    prior_price_low   = prior_prices.min()
    recent_price_high = recent_prices.max()
    prior_price_high  = prior_prices.max()

    recent_obv_low    = recent_obv.min()
    prior_obv_low     = prior_obv.min()
    recent_obv_high   = recent_obv.max()
    prior_obv_high    = prior_obv.max()

    avg_recent_vol = recent_volumes.mean()
    avg_prior_vol  = prior_volumes.mean()

    curr_price = prices.iloc[-1]

    # ── Bullish Price-Volume Divergence ─────────────────────────────────────
    # Price lower low + OBV higher low = smart money accumulating on dips
    bullish_pv_div = recent_price_low < prior_price_low and recent_obv_low > prior_obv_low

    # Volume decreasing on down moves (selling pressure drying up)
    down_candles_recent = df_ltf[df_ltf['Close'] < df_ltf['Open']].iloc[-lookback:]
    down_candles_prior  = df_ltf[df_ltf['Close'] < df_ltf['Open']].iloc[-lookback * 2:-lookback]

    avg_down_vol_recent = down_candles_recent['Volume'].mean() if len(down_candles_recent) > 0 else avg_recent_vol
    avg_down_vol_prior  = down_candles_prior['Volume'].mean()  if len(down_candles_prior) > 0  else avg_prior_vol

    down_vol_decreasing = avg_down_vol_recent < avg_down_vol_prior * 0.85

    if bullish_pv_div and down_vol_decreasing:
        score += 45
        signals.append("✅ STRONG Bullish P/V Divergence — Price lower low + OBV higher low + Declining sell volume!")
    elif bullish_pv_div:
        score += 30
        signals.append("✅ Bullish P/V Divergence — Price lower low but OBV higher low (smart money accumulating)")
    elif down_vol_decreasing:
        score += 15
        signals.append("✅ Sell-side volume declining — bearish conviction weakening")
    else:
        signals.append("❌ No bullish price-volume divergence detected")

    # ── Bearish P/V Divergence (warn only for long trades) ──────────────────
    bearish_pv_div = recent_price_high > prior_price_high and recent_obv_high < prior_obv_high
    if bearish_pv_div:
        score -= 20
        signals.append("⚠️ Bearish P/V Divergence — Price higher high but OBV not confirming (distribution!)")

    # ── OBV trend direction ─────────────────────────────────────────────────
    obv_slope_5  = obv_series.iloc[-1] - obv_series.iloc[-5]
    obv_slope_10 = obv_series.iloc[-1] - obv_series.iloc[-10]

    if obv_slope_5 > 0 and obv_slope_10 > 0:
        score += 20
        signals.append("✅ OBV rising consistently — accumulation in progress")
    elif obv_slope_5 > 0:
        score += 10
        signals.append("✅ OBV short-term rising — early accumulation signal")
    else:
        signals.append("❌ OBV declining — distribution / selling pressure")

    # ── Volume surge on up candles ──────────────────────────────────────────
    up_candles = df_ltf[df_ltf['Close'] > df_ltf['Open']].iloc[-lookback:]
    if len(up_candles) > 0:
        avg_up_vol = up_candles['Volume'].mean()
        up_down_ratio = avg_up_vol / (avg_down_vol_recent + 1e-10)
        if up_down_ratio >= 1.5:
            score += 15
            signals.append(f"✅ Up-candle volume {up_down_ratio:.1f}x down-candle volume — Buying power dominant")
        elif up_down_ratio >= 1.0:
            score += 8
            signals.append(f"✅ Up-candle volume slightly higher than down ({up_down_ratio:.1f}x)")
        else:
            signals.append(f"⚠️ Down-candle volume dominant ({1/up_down_ratio:.1f}x) — Selling pressure")

    # ── HTF trend context ───────────────────────────────────────────────────
    df_htf['EMA50'] = ema(df_htf['Close'], 50)
    htf_bullish     = df_htf['Close'].iloc[-1] > df_htf['EMA50'].iloc[-1]
    if htf_bullish:
        score += 10
        signals.append("✅ HTF uptrend — bullish divergence more reliable")
    else:
        signals.append("⚠️ HTF downtrend — divergence trade is counter-trend")

    # ── Support zone check ──────────────────────────────────────────────────
    swing_high, swing_low = swing_high_low(df_htf)
    support_band = swing_low * 1.08
    if curr_price <= support_band:
        score += 10
        signals.append(f"✅ Price near HTF support ₹{swing_low:.2f} — Divergence more powerful here")

    # ── Trade levels ────────────────────────────────────────────────────────
    atr_val = atr(df_ltf).iloc[-1]
    sl      = round(swing_low - 0.5 * atr_val, 2)
    target  = round(curr_price + 3.5 * atr_val, 2)
    rr      = round((target - curr_price) / max(curr_price - sl, 0.01), 2)

    obv_curr = obv_series.iloc[-1]
    signals.append(f"📐 OBV: {obv_curr:,.0f} | Sell vol ratio: {avg_down_vol_recent/avg_down_vol_prior:.2f} | R:R = 1:{rr}")

    if score >= 35:
        return {
            "Entry":          round(curr_price, 2),
            "SL":             sl,
            "Target":         target,
            "strategy_score": min(score, 100),
            "signals":        signals,
            "strategy_name":  "Price & Volume Divergence"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 9 — PRICE & RSI DIVERGENCE (ENHANCED)
# ─────────────────────────────────────────────

def strategy_price_rsi_divergence(df_htf, df_ltf):
    """
    Enhanced Price & RSI Divergence — Catches high-probability reversals.

    This is a deeper implementation than Strategy 5 (basic RSI divergence):
    - Scans MULTIPLE lookback windows (5, 8, 13 bars) for divergence
    - Scores divergence strength based on magnitude of price vs RSI gap
    - Adds MACD histogram confirmation
    - Adds Stochastic RSI for overbought/oversold confirmation
    - Adds candlestick reversal pattern detection at the divergence point
    - Distinguishes between 'classic' and 'hidden' divergences

    Bullish Classic:  Price LL + RSI HL → reversal up
    Bearish Classic:  Price HH + RSI LH → reversal down
    Hidden Bullish:   Price HL + RSI LL → trend continuation up
    Hidden Bearish:   Price LH + RSI HH → trend continuation down
    """
    signals = []
    score   = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # ── RSI & Stochastic RSI ────────────────────────────────────────────────
    df_ltf['RSI'] = rsi(df_ltf, 14)

    # Stochastic RSI: normalized RSI oscillator (0–100)
    rsi_series  = df_ltf['RSI']
    stoch_window = 14
    rsi_low  = rsi_series.rolling(stoch_window).min()
    rsi_high = rsi_series.rolling(stoch_window).max()
    stoch_rsi = 100 * (rsi_series - rsi_low) / (rsi_high - rsi_low + 1e-10)
    df_ltf['StochRSI'] = stoch_rsi

    curr_rsi      = df_ltf['RSI'].iloc[-1]
    curr_stoch    = df_ltf['StochRSI'].iloc[-1]
    curr_price    = df_ltf['Close'].iloc[-1]

    # ── Multi-window divergence scan ────────────────────────────────────────
    divergences_found = []

    for lookback in [5, 8, 13]:
        if len(df_ltf) < lookback * 2 + 5:
            continue

        p_curr  = df_ltf['Close'].iloc[-1]
        p_prev  = df_ltf['Close'].iloc[-(lookback + 1)]
        r_curr  = df_ltf['RSI'].iloc[-1]
        r_prev  = df_ltf['RSI'].iloc[-(lookback + 1)]

        p_change   = (p_curr - p_prev) / (abs(p_prev) + 1e-10)
        r_change   = (r_curr - r_prev)
        divergence_magnitude = abs(p_change * 100 - r_change / 10)

        # ── Classic Bullish: Price LL + RSI HL ──────────────────────────────
        if p_curr < p_prev and r_curr > r_prev and curr_rsi < 50:
            divergences_found.append(('classic_bullish', lookback, divergence_magnitude))

        # ── Classic Bearish: Price HH + RSI LH ──────────────────────────────
        elif p_curr > p_prev and r_curr < r_prev and curr_rsi > 50:
            divergences_found.append(('classic_bearish', lookback, divergence_magnitude))

        # ── Hidden Bullish: Price HL + RSI LL (trend continuation) ──────────
        elif p_curr > p_prev and r_curr < r_prev and curr_rsi < 50:
            divergences_found.append(('hidden_bullish', lookback, divergence_magnitude))

        # ── Hidden Bearish: Price LH + RSI HH (trend continuation) ──────────
        elif p_curr < p_prev and r_curr > r_prev and curr_rsi > 50:
            divergences_found.append(('hidden_bearish', lookback, divergence_magnitude))

    # Score based on best divergence found
    best_div = None
    if divergences_found:
        # Sort by magnitude descending
        divergences_found.sort(key=lambda x: x[2], reverse=True)
        best_div = divergences_found[0]
        div_type, div_lookback, div_mag = best_div

        if div_type == 'classic_bullish':
            base_score = 40
            score += base_score + min(int(div_mag * 2), 20)
            signals.append(f"✅ CLASSIC BULLISH RSI Divergence (window: {div_lookback} bars, magnitude: {div_mag:.2f}) — Reversal signal!")
        elif div_type == 'hidden_bullish':
            base_score = 25
            score += base_score + min(int(div_mag), 15)
            signals.append(f"✅ HIDDEN BULLISH RSI Divergence (window: {div_lookback} bars) — Trend continuation up!")
        elif div_type == 'classic_bearish':
            score -= 10
            signals.append(f"⚠️ Classic BEARISH divergence found (window: {div_lookback}) — Not suitable for longs")
        elif div_type == 'hidden_bearish':
            score -= 5
            signals.append(f"⚠️ Hidden BEARISH divergence (window: {div_lookback}) — Trend continuation down")

        # Bonus if MULTIPLE timeframes confirm
        bullish_count = sum(1 for d in divergences_found if 'bullish' in d[0])
        if bullish_count >= 2:
            score += 15
            signals.append(f"✅ Divergence confirmed across {bullish_count} windows — HIGH reliability!")
    else:
        signals.append("❌ No RSI divergence detected in any window")

    # ── RSI zone analysis ───────────────────────────────────────────────────
    if curr_rsi < 30:
        score += 20
        signals.append(f"✅ RSI deeply oversold ({curr_rsi:.1f}) — Reversal power amplified")
    elif curr_rsi < 40:
        score += 12
        signals.append(f"✅ RSI oversold zone ({curr_rsi:.1f})")
    elif curr_rsi < 50:
        score += 5
        signals.append(f"✅ RSI below 50 ({curr_rsi:.1f}) — Bearish but may bounce")
    else:
        signals.append(f"⚠️ RSI {curr_rsi:.1f} — Divergence less powerful above 50")

    # ── Stochastic RSI confirmation ─────────────────────────────────────────
    if curr_stoch < 20:
        score += 15
        signals.append(f"✅ StochRSI oversold ({curr_stoch:.1f}) — Double oversold confirmation!")
    elif curr_stoch < 40:
        score += 8
        signals.append(f"✅ StochRSI low ({curr_stoch:.1f}) — RSI momentum compressed")
    else:
        signals.append(f"⚠️ StochRSI {curr_stoch:.1f} — No extreme reading")

    # ── MACD histogram momentum shift ──────────────────────────────────────
    macd_line, sig_line, histogram = macd(df_ltf)
    hist_curr  = histogram.iloc[-1]
    hist_prev  = histogram.iloc[-2]
    hist_prev2 = histogram.iloc[-3]

    if hist_curr > hist_prev > hist_prev2:
        score += 15
        signals.append("✅ MACD histogram rising 3 consecutive bars — Momentum confirmed!")
    elif hist_curr > hist_prev:
        score += 8
        signals.append("✅ MACD histogram turning up — Momentum shifting")
    elif hist_curr > 0 and macd_line.iloc[-1] > sig_line.iloc[-1]:
        score += 5
        signals.append("✅ MACD bullish (above signal)")
    else:
        signals.append("⚠️ MACD not confirming — wait for histogram to rise")

    # ── Candlestick reversal pattern at divergence point ────────────────────
    last_candle     = df_ltf.iloc[-1]
    prev_candle     = df_ltf.iloc[-2]
    body_size       = abs(last_candle['Close'] - last_candle['Open'])
    candle_range    = last_candle['High'] - last_candle['Low']
    lower_wick      = min(last_candle['Close'], last_candle['Open']) - last_candle['Low']
    upper_wick      = last_candle['High'] - max(last_candle['Close'], last_candle['Open'])
    is_bullish      = last_candle['Close'] > last_candle['Open']

    # Hammer (bullish reversal): long lower wick, small body, at bottom
    is_hammer = (lower_wick > 2 * body_size and candle_range > 0 and
                 lower_wick / candle_range > 0.6 and curr_rsi < 50)

    # Bullish engulfing: current green candle engulfs previous red candle
    is_engulfing = (is_bullish and
                    prev_candle['Close'] < prev_candle['Open'] and
                    last_candle['Open'] < prev_candle['Close'] and
                    last_candle['Close'] > prev_candle['Open'])

    # Piercing / strong close off lows
    strong_recovery = (is_bullish and
                       last_candle['Low'] < prev_candle['Low'] and
                       last_candle['Close'] > (last_candle['High'] + last_candle['Low']) / 2)

    if is_hammer:
        score += 15
        signals.append("✅ Hammer candlestick at divergence point — High-confidence reversal!")
    elif is_engulfing:
        score += 12
        signals.append("✅ Bullish engulfing at divergence — Buyers overwhelmed sellers!")
    elif strong_recovery:
        score += 8
        signals.append("✅ Strong recovery candle — Price rejected lows")

    # ── HTF context ─────────────────────────────────────────────────────────
    df_htf['EMA200'] = ema(df_htf['Close'], 200)
    df_htf['EMA50']  = ema(df_htf['Close'], 50)
    htf_price        = df_htf['Close'].iloc[-1]

    if htf_price > df_htf['EMA200'].iloc[-1]:
        score += 10
        signals.append("✅ HTF: Above EMA200 — Long-term bullish structure intact")
    else:
        signals.append("⚠️ HTF: Below EMA200 — Counter-trend divergence trade (smaller size)")

    # ── Trade levels ────────────────────────────────────────────────────────
    swing_high, swing_low = swing_high_low(df_htf)
    atr_val = atr(df_ltf).iloc[-1]

    sl     = round(curr_price - 2.0 * atr_val, 2)
    # Use nearest resistance as target
    next_resistance = df_ltf['High'].rolling(20).max().iloc[-5]  # recent high
    target = round(max(next_resistance, curr_price + 3.5 * atr_val), 2)
    rr     = round((target - curr_price) / max(curr_price - sl, 0.01), 2)

    signals.append(f"📐 RSI: {curr_rsi:.1f} | StochRSI: {curr_stoch:.1f} | Divergences: {len(divergences_found)} | R:R = 1:{rr}")

    if score >= 45:
        return {
            "Entry":          round(curr_price, 2),
            "SL":             sl,
            "Target":         target,
            "strategy_score": min(score, 100),
            "signals":        signals,
            "strategy_name":  "Price & RSI Divergence"
        }
    return None


# ─────────────────────────────────────────────
#  STRATEGY 10 — MARKET CONDITION SCANNER
#  Overbought / Oversold / Fair Value
#  + Nearest Support & Resistance Zones
# ─────────────────────────────────────────────

def _find_sr_zones(df, lookback=120, min_touches=2, zone_tolerance_pct=0.5):
    """
    Identify significant support and resistance zones from price history.

    Method:
      1. Collect all swing highs and swing lows using a rolling pivot approach.
      2. Cluster nearby levels (within zone_tolerance_pct %) together —
         a level touched multiple times is a strong zone.
      3. Return sorted lists of (price_level, strength, touch_count).

    Args:
        df              : OHLCV DataFrame
        lookback        : how many bars back to scan
        min_touches     : minimum times a level must be tested to qualify
        zone_tolerance_pct : % band within which two levels are merged

    Returns:
        supports    : list of dicts [{level, strength, touches, type}]
        resistances : list of dicts [{level, strength, touches, type}]
    """
    data = df.tail(lookback).copy().reset_index(drop=True)
    n    = len(data)

    pivot_highs = []
    pivot_lows  = []
    wing        = 3  # bars each side to qualify as a pivot

    for i in range(wing, n - wing):
        # Pivot high: highest point in a window of (wing * 2 + 1) bars
        if data['High'].iloc[i] == data['High'].iloc[i - wing: i + wing + 1].max():
            pivot_highs.append(data['High'].iloc[i])
        # Pivot low: lowest point in same window
        if data['Low'].iloc[i] == data['Low'].iloc[i - wing: i + wing + 1].min():
            pivot_lows.append(data['Low'].iloc[i])

    # Also add round-number psychological levels near current price
    curr_price = data['Close'].iloc[-1]
    magnitude  = 10 ** (len(str(int(curr_price))) - 2)   # e.g. ₹1543 → magnitude 100
    round_levels = [
        round(curr_price / magnitude) * magnitude + i * magnitude
        for i in range(-5, 6)
        if abs(round(curr_price / magnitude) * magnitude + i * magnitude - curr_price) / curr_price < 0.15
    ]

    all_highs = pivot_highs + [l for l in round_levels if l > curr_price]
    all_lows  = pivot_lows  + [l for l in round_levels if l < curr_price]

    def cluster_levels(levels, tolerance_pct):
        """Merge nearby levels and count how many times each cluster was tested."""
        if not levels:
            return []
        levels_sorted = sorted(set(levels))
        clusters = []
        current_cluster = [levels_sorted[0]]

        for lvl in levels_sorted[1:]:
            if (lvl - current_cluster[-1]) / (current_cluster[0] + 1e-10) * 100 <= tolerance_pct:
                current_cluster.append(lvl)
            else:
                clusters.append(current_cluster)
                current_cluster = [lvl]
        clusters.append(current_cluster)

        result = []
        for c in clusters:
            avg_level = sum(c) / len(c)
            touches   = len(c)
            # Strength: based on number of touches + proximity to key Fib levels
            strength  = min(touches * 20, 80) + (20 if touches >= 3 else 0)
            result.append({
                "level":   round(avg_level, 2),
                "touches": touches,
                "strength": min(strength, 100),
            })

        return [r for r in result if r["touches"] >= min_touches]

    raw_resistances = cluster_levels(all_highs, zone_tolerance_pct)
    raw_supports    = cluster_levels(all_lows,  zone_tolerance_pct)

    # Tag type
    for r in raw_resistances: r["type"] = "Resistance"
    for s in raw_supports:    s["type"] = "Support"

    # Sort by proximity to current price
    resistances = sorted(
        [r for r in raw_resistances if r["level"] > curr_price],
        key=lambda x: x["level"]
    )
    supports = sorted(
        [s for s in raw_supports if s["level"] < curr_price],
        key=lambda x: x["level"],
        reverse=True
    )

    return supports, resistances


def _market_condition(
    rsi_val, stoch_rsi_val, bb_position,
    price, vwap_val, ema20, ema50, ema200,
    atr_val
):
    """
    Determine market condition using 6 indicators with weighted scoring.

    Returns: condition_label, condition_score (-100 to +100), breakdown dict
      +70 to +100 → OVERBOUGHT
      +30 to +69  → MILDLY OVERBOUGHT
      -29 to +29  → FAIR VALUE
      -30 to -69  → MILDLY OVERSOLD
      -70 to -100 → OVERSOLD
    """
    score = 0
    breakdown = {}

    # ── 1. RSI (weight: 25) ──────────────────────────────────────────────────
    if rsi_val >= 75:
        rsi_score = 25
        rsi_label = f"OVERBOUGHT ({rsi_val:.1f})"
    elif rsi_val >= 65:
        rsi_score = 15
        rsi_label = f"Mildly OB ({rsi_val:.1f})"
    elif rsi_val >= 55:
        rsi_score = 5
        rsi_label = f"Neutral-High ({rsi_val:.1f})"
    elif rsi_val >= 45:
        rsi_score = 0
        rsi_label = f"Neutral ({rsi_val:.1f})"
    elif rsi_val >= 35:
        rsi_score = -5
        rsi_label = f"Neutral-Low ({rsi_val:.1f})"
    elif rsi_val >= 25:
        rsi_score = -15
        rsi_label = f"Mildly OS ({rsi_val:.1f})"
    else:
        rsi_score = -25
        rsi_label = f"OVERSOLD ({rsi_val:.1f})"
    score += rsi_score
    breakdown["RSI"] = {"value": round(rsi_val, 1), "score": rsi_score, "label": rsi_label}

    # ── 2. Stochastic RSI (weight: 20) ───────────────────────────────────────
    if stoch_rsi_val >= 85:
        srsi_score = 20
        srsi_label = f"OVERBOUGHT ({stoch_rsi_val:.1f})"
    elif stoch_rsi_val >= 70:
        srsi_score = 12
        srsi_label = f"Mildly OB ({stoch_rsi_val:.1f})"
    elif stoch_rsi_val >= 55:
        srsi_score = 4
        srsi_label = f"Neutral-High ({stoch_rsi_val:.1f})"
    elif stoch_rsi_val >= 45:
        srsi_score = 0
        srsi_label = f"Neutral ({stoch_rsi_val:.1f})"
    elif stoch_rsi_val >= 30:
        srsi_score = -4
        srsi_label = f"Neutral-Low ({stoch_rsi_val:.1f})"
    elif stoch_rsi_val >= 15:
        srsi_score = -12
        srsi_label = f"Mildly OS ({stoch_rsi_val:.1f})"
    else:
        srsi_score = -20
        srsi_label = f"OVERSOLD ({stoch_rsi_val:.1f})"
    score += srsi_score
    breakdown["Stoch RSI"] = {"value": round(stoch_rsi_val, 1), "score": srsi_score, "label": srsi_label}

    # ── 3. Bollinger Band position (weight: 20) ───────────────────────────────
    # bb_position: 0 = at lower band, 0.5 = at midband, 1.0 = at upper band
    if bb_position >= 0.95:
        bb_score = 20
        bb_label = f"Above upper band ({bb_position:.2f})"
    elif bb_position >= 0.80:
        bb_score = 12
        bb_label = f"Near upper band ({bb_position:.2f})"
    elif bb_position >= 0.60:
        bb_score = 4
        bb_label = f"Upper half ({bb_position:.2f})"
    elif bb_position >= 0.40:
        bb_score = 0
        bb_label = f"Mid-band ({bb_position:.2f})"
    elif bb_position >= 0.20:
        bb_score = -4
        bb_label = f"Lower half ({bb_position:.2f})"
    elif bb_position >= 0.05:
        bb_score = -12
        bb_label = f"Near lower band ({bb_position:.2f})"
    else:
        bb_score = -20
        bb_label = f"Below lower band ({bb_position:.2f})"
    score += bb_score
    breakdown["Bollinger Position"] = {"value": round(bb_position, 3), "score": bb_score, "label": bb_label}

    # ── 4. Price vs VWAP (weight: 15) ────────────────────────────────────────
    vwap_gap_pct = (price - vwap_val) / (vwap_val + 1e-10) * 100
    if vwap_gap_pct >= 5:
        vwap_score = 15
        vwap_label = f"Far above VWAP (+{vwap_gap_pct:.2f}%)"
    elif vwap_gap_pct >= 2:
        vwap_score = 8
        vwap_label = f"Above VWAP (+{vwap_gap_pct:.2f}%)"
    elif vwap_gap_pct >= -2:
        vwap_score = 0
        vwap_label = f"Near VWAP ({vwap_gap_pct:.2f}%)"
    elif vwap_gap_pct >= -5:
        vwap_score = -8
        vwap_label = f"Below VWAP ({vwap_gap_pct:.2f}%)"
    else:
        vwap_score = -15
        vwap_label = f"Far below VWAP ({vwap_gap_pct:.2f}%)"
    score += vwap_score
    breakdown["Price vs VWAP"] = {"value": round(vwap_gap_pct, 2), "score": vwap_score, "label": vwap_label}

    # ── 5. EMA structure (weight: 10) ────────────────────────────────────────
    if price > ema20 > ema50 > ema200:
        ema_score = 10
        ema_label = "Full bull stack (Price > EMA20 > EMA50 > EMA200)"
    elif price > ema50 > ema200:
        ema_score = 6
        ema_label = "Above EMA50 & EMA200 — uptrend"
    elif price > ema200:
        ema_score = 2
        ema_label = "Above EMA200 only — weak bull"
    elif price < ema200 and price > ema50:
        ema_score = -2
        ema_label = "Below EMA200, above EMA50 — mixed"
    elif price < ema50 < ema200:
        ema_score = -6
        ema_label = "Below EMA50 & EMA200 — downtrend"
    else:
        ema_score = -10
        ema_label = "Full bear stack — strong downtrend"
    score += ema_score
    breakdown["EMA Structure"] = {"score": ema_score, "label": ema_label}

    # ── 6. Price distance from EMA20 (mean reversion gauge, weight: 10) ──────
    ema20_gap_pct = (price - ema20) / (ema20 + 1e-10) * 100
    if ema20_gap_pct >= 8:
        mr_score = 10
        mr_label = f"Extremely extended above EMA20 (+{ema20_gap_pct:.2f}%) — mean reversion risk HIGH"
    elif ema20_gap_pct >= 4:
        mr_score = 5
        mr_label = f"Extended above EMA20 (+{ema20_gap_pct:.2f}%)"
    elif ema20_gap_pct >= -4:
        mr_score = 0
        mr_label = f"Near EMA20 ({ema20_gap_pct:.2f}%) — fair value zone"
    elif ema20_gap_pct >= -8:
        mr_score = -5
        mr_label = f"Extended below EMA20 ({ema20_gap_pct:.2f}%)"
    else:
        mr_score = -10
        mr_label = f"Extremely depressed below EMA20 ({ema20_gap_pct:.2f}%) — snap-back risk HIGH"
    score += mr_score
    breakdown["EMA20 Extension"] = {"value": round(ema20_gap_pct, 2), "score": mr_score, "label": mr_label}

    # ── Classify condition ───────────────────────────────────────────────────
    if score >= 70:
        condition = "🔴 OVERBOUGHT"
        action    = "AVOID BUYING — Wait for pullback to fair value or support zone"
    elif score >= 30:
        condition = "🟠 MILDLY OVERBOUGHT"
        action    = "CAUTION — Only enter on strong momentum confirmation; tight stop"
    elif score >= -29:
        condition = "🟢 FAIR VALUE"
        action    = "IDEAL ZONE — Best risk:reward for new entries"
    elif score >= -69:
        condition = "🔵 MILDLY OVERSOLD"
        action    = "WATCH — Look for reversal signals; prepare buy levels"
    else:
        condition = "💜 OVERSOLD"
        action    = "HIGH ALERT — Strong bounce candidate; wait for confirmation candle"

    return condition, score, action, breakdown


def strategy_market_condition_scanner(df_htf, df_ltf):
    """
    Market Condition Scanner — Strategy 10

    For any ticker, answers three key questions:
      1. Is this stock OVERBOUGHT, OVERSOLD, or at FAIR VALUE right now?
      2. Where is the NEAREST SUPPORT zone below CMP?
      3. Where is the NEAREST RESISTANCE zone above CMP?

    Uses 6 indicators for condition assessment:
      - RSI (14)
      - Stochastic RSI
      - Bollinger Band position (0 = lower band, 1 = upper band)
      - Price vs VWAP deviation %
      - EMA stack structure (EMA20/50/200)
      - Price extension from EMA20 (mean-reversion gauge)

    Support/Resistance detection uses:
      - Swing pivot highs and lows (120-bar lookback)
      - Psychological round-number levels
      - Fibonacci levels from recent major swing
      - EMA lines as dynamic S/R
      - Volume Profile approximation (high-volume price nodes)

    Trade logic:
      - OVERSOLD at Support Zone  → BUY setup (highest probability)
      - FAIR VALUE near Support   → BUY setup (good probability)
      - FAIR VALUE rising         → HOLD / add
      - OVERBOUGHT near Resistance→ EXIT / AVOID new longs
      - OVERSOLD at Resistance    → Avoid (stuck stock)
    """
    signals = []
    score   = 0

    df_htf = df_htf.copy()
    df_ltf = df_ltf.copy()

    # ── Compute all indicators ───────────────────────────────────────────────
    df_ltf['RSI'] = rsi(df_ltf, 14)

    rsi_series   = df_ltf['RSI']
    stoch_win    = 14
    rsi_min      = rsi_series.rolling(stoch_win).min()
    rsi_max      = rsi_series.rolling(stoch_win).max()
    stoch_rsi_s  = 100 * (rsi_series - rsi_min) / (rsi_max - rsi_min + 1e-10)
    df_ltf['StochRSI'] = stoch_rsi_s

    upper_bb, mid_bb, lower_bb, bw = bollinger_bands(df_ltf)
    curr_upper = upper_bb.iloc[-1]
    curr_lower = lower_bb.iloc[-1]
    curr_mid   = mid_bb.iloc[-1]

    df_ltf['VWAP']  = vwap(df_ltf)
    df_ltf['EMA20'] = ema(df_ltf['Close'], 20)
    df_ltf['EMA50'] = ema(df_ltf['Close'], 50)

    df_htf['EMA200'] = ema(df_htf['Close'], 200)

    curr_price    = df_ltf['Close'].iloc[-1]
    curr_rsi      = df_ltf['RSI'].iloc[-1]
    curr_stoch    = df_ltf['StochRSI'].iloc[-1]
    curr_vwap     = df_ltf['VWAP'].iloc[-1]
    curr_ema20    = df_ltf['EMA20'].iloc[-1]
    curr_ema50    = df_ltf['EMA50'].iloc[-1]
    curr_ema200   = df_htf['EMA200'].iloc[-1]
    curr_atr      = atr(df_ltf).iloc[-1]

    # Bollinger position: normalised 0 (lower) → 1 (upper)
    bb_pos = (curr_price - curr_lower) / (curr_upper - curr_lower + 1e-10)
    bb_pos = max(0.0, min(1.0, bb_pos))   # clamp

    # ── Market condition assessment ──────────────────────────────────────────
    condition, cond_score, action, breakdown = _market_condition(
        curr_rsi, curr_stoch, bb_pos,
        curr_price, curr_vwap,
        curr_ema20, curr_ema50, curr_ema200,
        curr_atr
    )

    # ── Support & Resistance zone detection ──────────────────────────────────
    supports, resistances = _find_sr_zones(df_htf, lookback=120, min_touches=2)

    # Also add EMA lines as dynamic S/R
    ema_levels = []
    for ema_period, ema_val, ema_name in [
        (20, curr_ema20, "EMA20"), (50, curr_ema50, "EMA50"), (200, curr_ema200, "EMA200")
    ]:
        if ema_val < curr_price:
            ema_levels.append({"level": round(ema_val, 2), "touches": 2, "strength": 60, "type": "Support (EMA)", "label": ema_name})
        else:
            ema_levels.append({"level": round(ema_val, 2), "touches": 2, "strength": 60, "type": "Resistance (EMA)", "label": ema_name})

    # Add VWAP as a dynamic level
    if curr_vwap < curr_price:
        ema_levels.append({"level": round(curr_vwap, 2), "touches": 3, "strength": 70, "type": "Support (VWAP)", "label": "VWAP"})
    else:
        ema_levels.append({"level": round(curr_vwap, 2), "touches": 3, "strength": 70, "type": "Resistance (VWAP)", "label": "VWAP"})

    # Add Fibonacci levels from the last major swing
    swing_high, swing_low = swing_high_low(df_htf, lookback=60)
    swing_size = swing_high - swing_low
    fib_levels_raw = [
        (swing_high - 0.236 * swing_size, "Fib 23.6%"),
        (swing_high - 0.382 * swing_size, "Fib 38.2%"),
        (swing_high - 0.500 * swing_size, "Fib 50.0%"),
        (swing_high - 0.618 * swing_size, "Fib 61.8%"),
        (swing_high - 0.786 * swing_size, "Fib 78.6%"),
    ]
    for fib_price, fib_name in fib_levels_raw:
        dist_pct = abs(fib_price - curr_price) / curr_price * 100
        if dist_pct <= 20:   # only include Fib levels within 20% of CMP
            if fib_price < curr_price:
                ema_levels.append({"level": round(fib_price, 2), "touches": 2, "strength": 65, "type": "Support (Fib)", "label": fib_name})
            else:
                ema_levels.append({"level": round(fib_price, 2), "touches": 2, "strength": 65, "type": "Resistance (Fib)", "label": fib_name})

    # Merge pivot S/R with dynamic levels
    all_support_levels = sorted(
        [{"level": s["level"], "touches": s["touches"], "strength": s["strength"],
          "type": "Support", "label": f"Pivot ({s['touches']} touches)"}
         for s in supports] +
        [l for l in ema_levels if "Support" in l["type"]],
        key=lambda x: x["level"],
        reverse=True   # closest below CMP first
    )

    all_resistance_levels = sorted(
        [{"level": r["level"], "touches": r["touches"], "strength": r["strength"],
          "type": "Resistance", "label": f"Pivot ({r['touches']} touches)"}
         for r in resistances] +
        [l for l in ema_levels if "Resistance" in l["type"]],
        key=lambda x: x["level"]  # closest above CMP first
    )

    # Pick the 3 nearest each side
    nearest_supports    = all_support_levels[:3]
    nearest_resistances = all_resistance_levels[:3]

    # ── Build signal output ───────────────────────────────────────────────────
    signals.append(f"═══════════════════════════════")
    signals.append(f"📍 CMP: ₹{curr_price:.2f}")
    signals.append(f"═══════════════════════════════")
    signals.append(f"")
    signals.append(f"📊 MARKET CONDITION: {condition}")
    signals.append(f"💡 Action: {action}")
    signals.append(f"📈 Condition Score: {cond_score:+d} / 100")
    signals.append(f"")
    signals.append(f"── Indicator Breakdown ──────────")

    for ind_name, ind_data in breakdown.items():
        score_str = f"{ind_data['score']:+d}"
        signals.append(f"  {ind_name}: {ind_data['label']}  [{score_str}]")

    signals.append(f"")
    signals.append(f"── Nearest SUPPORT Zones ────────")
    if nearest_supports:
        for i, sup in enumerate(nearest_supports, 1):
            dist_pct = (curr_price - sup["level"]) / curr_price * 100
            strength_bar = "█" * (sup["strength"] // 20)
            signals.append(
                f"  S{i}  ₹{sup['level']:.2f}  ({dist_pct:.1f}% below)  "
                f"Strength: {strength_bar} {sup['strength']}%  [{sup.get('label', sup['type'])}]"
            )
    else:
        signals.append("  ⚠️ No clear support zones found in recent history")

    signals.append(f"")
    signals.append(f"── Nearest RESISTANCE Zones ─────")
    if nearest_resistances:
        for i, res in enumerate(nearest_resistances, 1):
            dist_pct = (res["level"] - curr_price) / curr_price * 100
            strength_bar = "█" * (res["strength"] // 20)
            signals.append(
                f"  R{i}  ₹{res['level']:.2f}  ({dist_pct:.1f}% above)  "
                f"Strength: {strength_bar} {res['strength']}%  [{res.get('label', res['type'])}]"
            )
    else:
        signals.append("  ⚠️ No clear resistance zones found in recent history")

    signals.append(f"")
    signals.append(f"── Key Levels Summary ───────────")
    signals.append(f"  VWAP    : ₹{curr_vwap:.2f}")
    signals.append(f"  EMA20   : ₹{curr_ema20:.2f}")
    signals.append(f"  EMA50   : ₹{curr_ema50:.2f}")
    signals.append(f"  EMA200  : ₹{curr_ema200:.2f}  (HTF)")
    signals.append(f"  BB Upper: ₹{curr_upper:.2f}")
    signals.append(f"  BB Mid  : ₹{curr_mid:.2f}")
    signals.append(f"  BB Lower: ₹{curr_lower:.2f}")
    signals.append(f"  ATR(14) : ₹{curr_atr:.2f}")
    signals.append(f"  Swing H : ₹{swing_high:.2f}")
    signals.append(f"  Swing L : ₹{swing_low:.2f}")

    # ── Trade setup scoring ───────────────────────────────────────────────────
    # Best trade: OVERSOLD or FAIR VALUE + price near strong support
    if cond_score <= -30 and nearest_supports:
        nearest_sup_dist = (curr_price - nearest_supports[0]["level"]) / curr_price * 100
        if nearest_sup_dist <= 3.0:
            score = 85
            signals.append(f"\n🎯 TRADE SETUP: OVERSOLD at Support — HIGH probability long!")
        elif nearest_sup_dist <= 6.0:
            score = 70
            signals.append(f"\n🎯 TRADE SETUP: Oversold, approaching support — WATCH for entry")
        else:
            score = 50
            signals.append(f"\n⚠️ TRADE SETUP: Oversold but far from support ({nearest_sup_dist:.1f}%)")

    elif -29 <= cond_score <= 29 and nearest_supports:
        nearest_sup_dist = (curr_price - nearest_supports[0]["level"]) / curr_price * 100
        if nearest_sup_dist <= 2.0:
            score = 75
            signals.append(f"\n🎯 TRADE SETUP: Fair Value at Support — Good risk:reward entry")
        else:
            score = 55
            signals.append(f"\n✅ TRADE SETUP: Fair Value — Neutral zone, wait for signal")

    elif cond_score >= 30:
        score = 20
        signals.append(f"\n⛔ TRADE SETUP: OVERBOUGHT — Avoid new longs, wait for pullback")
    else:
        score = 40

    # ── Entry / SL / Target from nearest S/R ─────────────────────────────────
    entry  = round(curr_price, 2)

    if nearest_supports:
        sl = round(nearest_supports[0]["level"] - curr_atr * 0.3, 2)
    else:
        sl = round(curr_price - 2 * curr_atr, 2)

    if nearest_resistances:
        target = round(nearest_resistances[0]["level"] - curr_atr * 0.1, 2)
    else:
        target = round(curr_price + 3 * curr_atr, 2)

    rr_val = round((target - entry) / max(entry - sl, 0.01), 2)
    signals.append(f"📐 Nearest S/R based levels: Entry ₹{entry} | SL ₹{sl} | Target ₹{target} | R:R = 1:{rr_val}")

    return {
        "Entry":          entry,
        "SL":             sl,
        "Target":         target,
        "strategy_score": min(max(score, 0), 100),
        "signals":        signals,
        "strategy_name":  "Market Condition Scanner",
        # Extra data for UI rendering
        "condition":      condition,
        "cond_score":     cond_score,
        "action":         action,
        "nearest_supports":    nearest_supports,
        "nearest_resistances": nearest_resistances,
        "key_levels": {
            "vwap": round(curr_vwap, 2),
            "ema20": round(curr_ema20, 2),
            "ema50": round(curr_ema50, 2),
            "ema200": round(curr_ema200, 2),
            "bb_upper": round(curr_upper, 2),
            "bb_lower": round(curr_lower, 2),
            "atr": round(curr_atr, 2),
        }
    }


# ─────────────────────────────────────────────
#  STRATEGY REGISTRY
# ─────────────────────────────────────────────

STRATEGIES = {
    "RSI + MACD Combo":          strategy_rsi_macd,
    "EMA Crossover":             strategy_ema_crossover,
    "S&R Breakout":              strategy_sr_breakout,
    "Fibonacci Retracement":     strategy_fibonacci,
    "RSI Divergence":            strategy_rsi_divergence,
    "Bollinger Band Squeeze":    strategy_bollinger_squeeze,
    "Supertrend + VWAP":         strategy_supertrend_vwap,
    "Price & Volume Divergence": strategy_price_volume_divergence,
    "Price & RSI Divergence":    strategy_price_rsi_divergence,
    "Market Condition Scanner":  strategy_market_condition_scanner,
}


def analyze_symbol(df_htf, df_ltf, strategy_name="RSI + MACD Combo"):
    """
    Run the selected strategy on the given data.
    Returns trade dict or None.
    """
    fn = STRATEGIES.get(strategy_name)
    if fn is None:
        return None
    return fn(df_htf, df_ltf)