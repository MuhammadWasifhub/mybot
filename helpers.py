import pandas as pd

def get_margin_by_timeframe(tf):
    if tf == "1m":
        return 1.025  # 2.5% margin
    elif tf == "5m":
        return 1.02   # 2.0% margin
    elif tf == "15m":
        return 1.015  # 1.5% margin
    else:
        return 1.01   # default (1%)

def support_resistance_volume(df, timeframe):
    # Get margin based on timeframe
    margin = get_margin_by_timeframe(timeframe)

    # Support / Resistance Calculation
    recent_highs = df["high"].rolling(window=10).max()
    recent_lows = df["low"].rolling(window=10).min()
    resistance = recent_highs.iloc[-2]
    support = recent_lows.iloc[-2]
    price = df["close"].iloc[-1]

    # Price near support or resistance (dynamic margin)
    near_support = price <= support * margin
    near_resistance = price >= resistance * (2 - margin)

    # Volume Check
    avg_volume = df["volume"].rolling(window=20).mean().iloc[-1]
    current_volume = df["volume"].iloc[-1]
    volume_ok = current_volume > avg_volume

    # Trend Check
    prev_price = df["close"].iloc[-2]
    trend = "UP" if price > prev_price else "DOWN"

    # Candle Analysis
    last_candle_bullish = df["close"].iloc[-1] > df["open"].iloc[-1]
    last_candle_bearish = df["close"].iloc[-1] < df["open"].iloc[-1]

    # Signal Logic
    signal = "NO SIGNAL"
    if near_support and trend == "UP" and last_candle_bullish:
        signal = "LONG"
    elif near_resistance and trend == "DOWN" and last_candle_bearish:
        signal = "SHORT"


    return {
        "support": round(support, 5),
        "resistance": round(resistance, 5),
        "volume": round(current_volume, 2),
        "volume_ok": volume_ok,
        "near_support": near_support,
        "near_resistance": near_resistance,
        "signal": signal
    }
