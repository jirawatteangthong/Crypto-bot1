from utils import fetch_ohlcv, detect_choch

def get_fibo_zone():
    candles = fetch_ohlcv('15m')[-70:]
    choch = detect_choch(candles)
    if not choch:
        return None, None

    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]

    if choch == 'bullish':
        fibo_high = max(highs)
        fibo_low = min(lows)
        return {
            'trend': 'bullish',
            '61.8': fibo_low + (fibo_high - fibo_low) * 0.618,
            '78.6': fibo_low + (fibo_high - fibo_low) * 0.786,
            'tp': fibo_high,
            'sl': fibo_low
        }, 'bullish'
    else:
        fibo_high = max(highs)
        fibo_low = min(lows)
        return {
            'trend': 'bearish',
            '61.8': fibo_high - (fibo_high - fibo_low) * 0.618,
            '78.6': fibo_high - (fibo_high - fibo_low) * 0.786,
            'tp': fibo_low,
            'sl': fibo_high
        }, 'bearish'
