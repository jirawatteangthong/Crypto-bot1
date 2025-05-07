from utils import fetch_ohlcv

def get_fibo_zone():
    candles = fetch_ohlcv('15m')
    trend = 'bullish' if candles[-1][4] > candles[-2][4] else 'bearish'

    # จำลองการตรวจ CHoCH และ swing ล่าสุด
    if trend == 'bullish':
        low = min([c[3] for c in candles[-30:]])
        high = max([c[2] for c in candles[-30:]])
    else:
        high = max([c[2] for c in candles[-30:]])
        low = min([c[3] for c in candles[-30:]])

    fibo = {
        'trend': trend,
        'high': high,
        'low': low,
        '61.8': high - (high - low) * 0.618 if trend == 'bearish' else low + (high - low) * 0.618,
        '78.6': high - (high - low) * 0.786 if trend == 'bearish' else low + (high - low) * 0.786
    }
    return fibo, trend
