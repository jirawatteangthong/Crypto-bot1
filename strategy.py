from utils import fetch_ohlcv, detect_bos, detect_choch
from telegram import alert_choch_m15, alert_fibo_drawn

last_fibo = {'high': None, 'low': None, 'direction': None}

def get_fibo_zone():
    h1 = fetch_ohlcv('1h')[-200:]
    m15 = fetch_ohlcv('15m')[-70:]

    trend = detect_bos(h1)
    choch = detect_choch(m15)
    if not trend or not choch or choch != trend:
        return None

    highs = [c[2] for c in h1[-70:]]
    lows = [c[3] for c in h1[-70:]]
    high = max(highs)
    low = min(lows)

    alert_choch_m15(choch)
    alert_fibo_drawn(low, high)

    if trend == 'bullish':
        fibo = {
            'direction': 'long',
            'levels': {
                '61.8': low + 0.618 * (high - low),
                '78.6': low + 0.786 * (high - low),
                '33.3': low + 0.333 * (high - low)
            },
            'tp': high - 10,
            'sl': low - 10,
            'low': low,
            'high': high
        }
    else:
        fibo = {
            'direction': 'short',
            'levels': {
                '61.8': high - 0.618 * (high - low),
                '78.6': high - 0.786 * (high - low),
                '33.3': high - 0.333 * (high - low)
            },
            'tp': low + 10,
            'sl': high + 10,
            'low': high,
            'high': low
        }

    return fibo
