import pandas as pd

def calculate_adx(df, period=14):
    df = df.copy()

    df["tr"] = df[["high", "close"]].max(axis=1) - df[["low", "close"]].min(axis=1)
    df["+dm"] = df["high"].diff()
    df["-dm"] = df["low"].diff()

    df["+dm"] = df["+dm"].where((df["+dm"] > df["-dm"]) & (df["+dm"] > 0), 0.0)
    df["-dm"] = df["-dm"].where((df["-dm"] > df["+dm"]) & (df["-dm"] > 0), 0.0)

    atr = df["tr"].rolling(window=period).mean()
    plus_di = 100 * (df["+dm"].rolling(window=period).mean() / atr)
    minus_di = 100 * (df["-dm"].rolling(window=period).mean() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()
    
    signal = "NO SIGNAL"

    # Calculate final signal
    adx_value = adx.iloc[-1]
    plus_di_value = plus_di.iloc[-1]
    minus_di_value = minus_di.iloc[-1]

    if adx_value > 25:
        if plus_di_value > minus_di_value:
            signal = "LONG"
        elif minus_di_value > plus_di_value:
            signal = "SHORT"
    else:
        signal = None

    return {
        "adx": round(adx.iloc[-1], 2),
        "plus_di": round(plus_di.iloc[-1], 2),
        "minus_di": round(minus_di.iloc[-1], 2),
        "signal": signal,
    }