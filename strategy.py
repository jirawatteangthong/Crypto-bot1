import pandas as pd
from utils import get_ohlcv, detect_bos, get_swing_points, calculate_fibo_levels

def analyze_market():
    df = get_ohlcv()
    if df is None or len(df) < 50:
        return None

    trend = detect_bos(df)
    if not trend:
        return None

    swing_high, swing_low = get_swing_points(df, trend)
    fibo = calculate_fibo_levels(swing_high, swing_low, trend)

    current_price = df['close'].iloc[-1]

    if trend == 'uptrend' and current_price <= fibo['62%'] >= fibo['78.6%']:
        return {'side': 'buy', 'entry': fibo['62%'], 'sl': fibo['110%'], 'tp': fibo['tp']}
    elif trend == 'downtrend' and current_price >= fibo['62%'] <= fibo['78.6%']:
        return {'side': 'sell', 'entry': fibo['62%'], 'sl': fibo['110%'], 'tp': fibo['tp']}
    
    return None
