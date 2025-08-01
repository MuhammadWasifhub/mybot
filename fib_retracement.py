# def calculate_fibonacci_levels(df):
#     """
#     Calculate Fibonacci retracement levels and generate a signal if the current price
#     is near any major level. Suitable for HFT and short timeframes (1m–5m).
#     """

#     recent_high = df["high"].iloc[-50:].max()
#     recent_low = df["low"].iloc[-50:].min()

#     current_price = df["close"].iloc[-1]
#     prev_price = df["close"].iloc[-2]

#     diff = recent_high - recent_low

#     levels = {
#         "Fib 0.236": round(recent_high - 0.236 * diff, 5),
#         "Fib 0.382": round(recent_high - 0.382 * diff, 5),
#         "Fib 0.5": round(recent_high - 0.5 * diff, 5),
#         "Fib 0.618": round(recent_high - 0.618 * diff, 5),
#         "Fib 0.786": round(recent_high - 0.786 * diff, 5),
#     }

#     signal = "NO SIGNAL"
#     triggered_level = "None"
#     tolerance = diff * 0.01  # 1% tolerance for short-term signals

#     trend = "UP" if current_price > prev_price else "DOWN"
#     last_candle_bullish = df["close"].iloc[-1] > df["open"].iloc[-1]
#     last_candle_bearish = df["close"].iloc[-1] < df["open"].iloc[-1]

#     for level_name, level_price in levels.items():
#         if abs(current_price - level_price) <= tolerance:
#             if trend == "UP" and last_candle_bullish:
#                 signal = "LONG"
#                 triggered_level = level_name
#                 break
#             elif trend == "DOWN" and last_candle_bearish:
#                 signal = "SHORT"
#                 triggered_level = level_name
#                 break

#     return {
#         "swing_high": round(recent_high, 5),
#         "swing_low": round(recent_low, 5),
#         "levels": levels,
#         "current_price": round(current_price, 5),
#         "signal": signal,
#         "triggered_level": triggered_level
#     }

def calculate_fibonacci_levels(df):
    """
    Calculate Fibonacci retracement levels and generate a signal if the current price
    is near any major level. Suitable for HFT and short timeframes (1m–5m).
    """

    recent_high = df["high"].iloc[-50:].max()
    recent_low = df["low"].iloc[-50:].min()

    current_price = df["close"].iloc[-1]
    prev_price = df["close"].iloc[-2]
    diff = recent_high - recent_low

    levels = {
        "Fib 0.236": round(recent_high - 0.236 * diff, 5),
        "Fib 0.382": round(recent_high - 0.382 * diff, 5),
        "Fib 0.5": round(recent_high - 0.5 * diff, 5),
        "Fib 0.618": round(recent_high - 0.618 * diff, 5),
        "Fib 0.786": round(recent_high - 0.786 * diff, 5),
    }

    signal = "NO SIGNAL"
    triggered_level = "None"
    tolerance = max(diff * 0.015, 0.25)  # 1.5% tolerance, at least 0.25

    last_candle_bullish = df["close"].iloc[-1] > df["open"].iloc[-1]
    last_candle_bearish = df["close"].iloc[-1] < df["open"].iloc[-1]
    trend = "UP" if current_price > prev_price else "DOWN"

    for level_name, level_price in levels.items():
        # Check if price is within tolerance range of the level
        if level_price - tolerance <= current_price <= level_price + tolerance:
            # Either trend or candle must agree
            if trend == "UP" or last_candle_bullish:
                signal = "LONG"
                triggered_level = level_name
                break
            elif trend == "DOWN" or last_candle_bearish:
                signal = "SHORT"
                triggered_level = level_name
                break

    return {
        "swing_high": round(recent_high, 5),
        "swing_low": round(recent_low, 5),
        "levels": levels,
        "current_price": round(current_price, 5),
        "signal": signal,
        "triggered_level": triggered_level
    }