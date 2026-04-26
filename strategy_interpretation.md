# Strategy Interpretation Guide

This document explains how to read the strategy results and how the **Strategy Score** is calculated.

## Scoring Overview
The total score is based on three main components, with a maximum possible score of **65 points**.

| Component | Logic | Points |
| :--- | :--- | :--- |
| **Trend (EMA50)** | Above 50 EMA (Uptrend) | **15** |
| **Swing (Fibonacci)** | Proximity to Fibonacci retracement levels | **Up to 30** |
| **Momentum (RSI)** | RSI within healthy bounds (30 - 70) | **Up to 20** |

---

## Detailed Breakdown

### 1. Trend (EMA50)
*   **YES**: Price is above the 50-period Exponential Moving Average (EMA). Indicates an overall uptrend. (+15)
*   **NO**: Price is below the 50 EMA. Indicates a downtrend. (+0)

### 2. Swing (Fibonacci)
This measures how much the price has pulled back (retraced) from its recent high.
*   **YES (Strong Zone)**: Price is between 50% and 61.8% retracement. Ideal entering zone. (+30)
*   **YES (Good Zone)**: Price is between 61.8% and 78.6%. (+20)
*   **YES (Near Support)**: Price is between 78.6% and the recent low. (+12)
*   **YES (Just Above fib50)**: Price is slightly above the 50% level (within 5% of the total swing). (+10)
*   **MAYBE (Above fib50)**: Price is significantly above the 50% level (more than 5% away). (+5)
*   **NO**: Price has fallen below the 30-period low. (+0)

### 3. RSI Momentum
*   **Neutral (40-60)**: Best momentum for stable entry. (+20)
*   **Low (30-40)**: Potential bounce from oversold. (+10)
*   **High (60-70)**: High momentum, but watch for pullbacks. (+10)
*   **Extreme (<30 or >70)**: Danger zone (Overbought or Oversold). (+0)

---

## Your Specific Result Analysis
**Strategy Score: 20/65**

*   **YES: Above EMA50 (uptrend)**: Price is in a macro uptrend. (+15)
*   **MAYBE: Above fib50% ($661.60): 87.20**: The price is $87.20 above the $661.60 mark (50% retracement). Because it hasn't pulled back enough into the "buying zone," it only scores minimal points. (+5)
*   **NO: RSI Extreme (83.3)**: An RSI of 83.3 indicates the asset is heavily **overbought**. This is considered a high-risk entry, so it scores 0 points for momentum. (+0)

**Total Calculation:** 15 (EMA) + 5 (Fib) + 0 (RSI) = **20 / 65**
