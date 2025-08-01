import pandas as pd
import numpy as np

def generate_signal(df):
    # RSI calculation
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]

    # EMA9 calculation
    ema9 = df["close"].ewm(span=9, adjust=False).mean()
    last_ema9 = ema9.iloc[-1]
    prev_ema9 = ema9.iloc[-2]

    # SMA20 calculation
    sma20 = df["close"].rolling(window=20).mean()
    last_sma20 = sma20.iloc[-1]
    prev_sma20 = sma20.iloc[-2]

    # Bollinger Bands calculation
    stddev = df["close"].rolling(window=20).std()
    bb_upper = sma20 + (2 * stddev)
    bb_lower = sma20 - (2 * stddev)

    last_bb_upper = bb_upper.iloc[-1]
    last_bb_lower = bb_lower.iloc[-1]

    # Check EMA9 crosses SMA20 upward AND SMA20 is below current EMA9 (LONG condition)
    ema_cross_up = (prev_ema9 < prev_sma20) and (last_ema9 > last_sma20) and (last_sma20 < last_ema9)

    # Check EMA9 crosses SMA20 downward AND SMA20 is above current EMA9 (SHORT condition)
    ema_cross_down = (prev_ema9 > prev_sma20) and (last_ema9 < last_sma20) and (last_sma20 > last_ema9)

    # # Relaxed EMA crossover logic #New Logic
    # ema_cross_up = last_ema9 > last_sma20 and prev_ema9 <= prev_sma20
    # ema_cross_down = last_ema9 < last_sma20 and prev_ema9 >= prev_sma20

    # First decide signal by RSI logic
    if 10 <= last_rsi < 30:
        signal = "LONG"      # Oversold Healthy
    elif 30 <= last_rsi < 40:
        signal = "LONG"      # Oversold Weak
    elif 60 <= last_rsi < 70:
        signal = "SHORT"     # Overbought Weak
    elif 70 <= last_rsi <= 90:
        signal = "SHORT"     # Overbought Healthy
    elif 40 <= last_rsi < 60:
        signal = "NEUTRAL"
        # # Neutral RSI zone, decide by price action
        # if df["close"].iloc[-1] > df["open"].iloc[-1]:
        #     signal = "LONG"
        # else:
        #     signal = "SHORT"
    else:
        signal = "NO SIGNAL"

    # Override signal if crossover condition matches
    ema_signal = "NO SIGNAL" # Initialize to avoid UnboundLocalError
    if ema_cross_up:
        ema_signal = "LONG"
    elif ema_cross_down:
        ema_signal = "SHORT"

    # ema_signal = "NO SIGNAL" #New logic
    # ema_slope = last_ema9 - prev_ema9

    # if last_ema9 > last_sma20 and ema_slope > 0 and df["close"].iloc[-1] > last_ema9:
    #     ema_signal = "LONG"
    # elif last_ema9 < last_sma20 and ema_slope < 0 and df["close"].iloc[-1] < last_ema9:
    #     ema_signal = "SHORT"

    #Bollinger Bnads Signal Logic
    price = df["close"].iloc[-1]
    prev_close = df["close"].iloc[-2]
    prev_open = df["open"].iloc[-2]
    current_open = df["open"].iloc[-1]

    # Candle direction confirmation
    candle_green = price > current_open and prev_close < prev_open
    candle_red = price < current_open and prev_close > prev_open

    tolerance = max((last_bb_upper - last_bb_lower) * 0.002, 0.5)

    bb_signal = "NO SIGNAL"
    if price <= last_bb_lower + tolerance and candle_green:
        bb_signal = "LONG"
    elif price >= last_bb_upper - tolerance and candle_red:
        bb_signal = "SHORT"

    return {
        "rsi_signal": signal,
        "ema_signal": ema_signal,
        "bb_signal": bb_signal,
        "rsi": round(last_rsi, 2),
        "ema9": round(last_ema9, 5),
        "sma20": round(last_sma20, 5),
        "ema_cross_up": ema_cross_up,
        "ema_cross_down": ema_cross_down,
        "bb_upper": round(last_bb_upper, 5),
        "bb_lower": round(last_bb_lower, 5)
    }
