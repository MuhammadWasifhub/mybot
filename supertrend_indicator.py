import pandas as pd

def calculate_supertrend(df, period=10, multiplier=3.0):
    df = df.copy()
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()

    hl2 = (df['high'] + df['low']) / 2
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])
    df['Supertrend'] = True

    for i in range(1, len(df)):
        prev = i - 1
        if df['close'].iloc[i] > df['UpperBand'].iloc[prev]:
            df.loc[i, 'Supertrend'] = True
        elif df['close'].iloc[i] < df['LowerBand'].iloc[prev]:
            df.loc[i, 'Supertrend'] = False
        else:
            df.loc[i, 'Supertrend'] = df.loc[prev, 'Supertrend']
            if df.loc[i, 'Supertrend']:
                df.loc[i, 'LowerBand'] = min(df['LowerBand'].iloc[i], df['LowerBand'].iloc[prev])
            else:
                df.loc[i, 'UpperBand'] = max(df['UpperBand'].iloc[i], df['UpperBand'].iloc[prev])

    price = df['close'].iloc[-1]
    trend = df['Supertrend'].iloc[-1]
    upper = df['UpperBand'].iloc[-1]
    lower = df['LowerBand'].iloc[-1]
    tolerance = max((upper - lower) * 0.02, 0.15)  # Increased to 2% or min 0.15

    signal = "NO SIGNAL"
    if trend and price >= lower - tolerance:
        signal = "LONG"
    elif not trend and price <= upper + tolerance:
        signal = "SHORT"

    return {
        "supertrend_signal": signal,
        "upper_band": round(upper, 4),
        "lower_band": round(lower, 4),
        "trend": "UP" if trend else "DOWN"
    }

# def calculate_supertrend(df, period=10, multiplier=3.0):
#     """
#     SuperTrend indicator for scalping/trend following.
#     period: ATR calculation period
#     multiplier: ATR multiplier for bands
#     """

#     df = df.copy()

#     # Step 1: ATR Calculation
#     df['H-L'] = df['high'] - df['low']
#     df['H-PC'] = abs(df['high'] - df['close'].shift(1))
#     df['L-PC'] = abs(df['low'] - df['close'].shift(1))
#     df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
#     df['ATR'] = df['TR'].rolling(window=period).mean()

#     # Step 2: Bands Calculation
#     hl2 = (df['high'] + df['low']) / 2
#     df['UpperBand'] = hl2 + (multiplier * df['ATR'])
#     df['LowerBand'] = hl2 - (multiplier * df['ATR'])

#     # Step 3: Supertrend Calculation
#     df['Supertrend'] = True  # default trend is "Buy"

#     for current in range(1, len(df)):
#         previous = current - 1

#         if df.loc[current, 'close'] > df.loc[previous, 'UpperBand']:
#             df.loc[current, 'Supertrend'] = True

#         elif df.loc[current, 'close'] < df.loc[previous, 'LowerBand']:
#             df.loc[current, 'Supertrend'] = False

#         else:
#             df.loc[current, 'Supertrend'] = df.loc[previous, 'Supertrend']

#             if df.loc[current, 'Supertrend']:
#                 if df.loc[current, 'LowerBand'] < df.loc[previous, 'LowerBand']:
#                     df.loc[current, 'LowerBand'] = df.loc[previous, 'LowerBand']
#             else:
#                 if df.loc[current, 'UpperBand'] > df.loc[previous, 'UpperBand']:
#                     df.loc[current, 'UpperBand'] = df.loc[previous, 'UpperBand']

#     # Step 4: Signal calculation with HFT confirmation
#     price = df['close'].iloc[-1]
#     upper_band = df['UpperBand'].iloc[-1]
#     lower_band = df['LowerBand'].iloc[-1]
#     supertrend = df['Supertrend'].iloc[-1]
#     tolerance = (upper_band - lower_band) * 0.005  # 0.5% tolerance for HFT

#     signal = "NO SIGNAL"
#     if supertrend and price >= lower_band - tolerance:
#         signal = "LONG"  # Price above lower band in uptrend
#     elif not supertrend and price <= upper_band + tolerance:
#         signal = "SHORT"  # Price below upper band in downtrend

#     return {
#         "supertrend_signal": signal,
#         "upper_band": round(upper_band, 4),
#         "lower_band": round(lower_band, 4)
#     }

#     # # Step 4: Return final signal #Previous Code!!!
#     # signal = "LONG" if df.loc[df.index[-1], 'Supertrend'] else "SHORT"

#     # return {
#     #     "supertrend": signal,
#     #     "upper_band": round(df.loc[df.index[-1], 'UpperBand'], 4),
#     #     "lower_band": round(df.loc[df.index[-1], 'LowerBand'], 4)
#     # }