from utils import fetch_ohlcv, detect_bos, detect_choch

def get_fibo_zone():
    candles = fetch_ohlcv('1h')
    trend = detect_bos(candles)
    choch = detect_choch(candles)

    if not trend:
        return None, None, 'no_trend'
    if not choch or choch != trend:
        return None, trend, 'skip'

    # ใช้ swing ล่าสุดจาก 50 แท่ง H1
    highs = [c[2] for c in candles[-50:]]
    lows = [c[3] for c in candles[-50:]]
    swing_high = max(highs)
    swing_low = min(lows)

    if trend == 'bullish':
        fibo = {
            'direction': 'long',
            'levels': {
                '78.6': swing_low + 0.786 * (swing_high - swing_low),
                '61.8': swing_low + 0.618 * (swing_high - swing_low)
            },
            'tp': swing_low + 0.10 * (swing_high - swing_low),
            'sl': swing_high + 0.20 * (swing_high - swing_low)
        }
    else:
        fibo = {
            'direction': 'short',
            'levels': {
                '78.6': swing_high - 0.786 * (swing_high - swing_low),
                '61.8': swing_high - 0.618 * (swing_high - swing_low)
            },
            'tp': swing_high - 0.10 * (swing_high - swing_low),
            'sl': swing_low - 0.20 * (swing_high - swing_low)
        }

    return fibo, trend, 'ok'
