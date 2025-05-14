from utils import fetch_ohlcv, detect_bos, detect_choch

def get_fibo_zone():
    h1 = fetch_ohlcv('1h')
    m15 = fetch_ohlcv('15m')

    trend = detect_bos(h1)
    if not trend:
        return None, None, 'wait'

    choch_m15 = detect_choch(m15)
    if choch_m15 != ('bearish' if trend == 'bullish' else 'bullish'):
        return None, trend, 'wait'

    highs = [c[2] for c in h1[-70:]]
    lows = [c[3] for c in h1[-70:]]
    high = max(highs)
    low = min(lows)

    if trend == 'bullish':
        fibo = {
            'direction': 'long',
            'levels': {
                '78.6': low + 0.786 * (high - low),
                '61.8': low + 0.618 * (high - low),
                '10.0': low + 0.10 * (high - low),
                '110.0': low + 1.10 * (high - low)
            }
        }
    else:
        fibo = {
            'direction': 'short',
            'levels': {
                '78.6': high - 0.786 * (high - low),
                '61.8': high - 0.618 * (high - low),
                '10.0': high - 0.10 * (high - low),
                '110.0': high - 1.10 * (high - low)
            }
        }

    return fibo, trend, 'ok'
