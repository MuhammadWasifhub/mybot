import pandas as pd
import ta

def calculate_pine_signal(df, len=20, lookback=50):
    signal = "NO SIGNAL"  # Default value

    # Indicators
    df['ema_red'] = ta.trend.ema_indicator(df['close'], window=len)
    df['ema_purple'] = ta.trend.ema_indicator(df['close'], window=len * 2)

    # Support & Resistance
    df['support'] = df['low'].rolling(window=lookback).min()
    df['resistance'] = df['high'].rolling(window=lookback).max()

    # Previous EMAs for crossover check
    df['prev_ema_red'] = df['ema_red'].shift(1)
    df['prev_ema_purple'] = df['ema_purple'].shift(1)

    # Bullish condition (exact from Pine Script)
    df['bullish'] = (
        (df['prev_ema_red'] <= df['prev_ema_purple']) &
        (df['ema_red'] > df['ema_purple']) &
        (df['close'] > df['support'])
    )

    # Bearish condition (exact from Pine Script)
    df['bearish'] = (
        (df['prev_ema_red'] >= df['prev_ema_purple']) &
        (df['ema_red'] < df['ema_purple']) &
        (df['close'] < df['resistance'])
    )

    # Get latest signal
    latest = df.iloc[-1]

    if latest['bullish']:
        signal = "LONG"
    elif latest['bearish']:
        signal = "SHORT"

    return signal