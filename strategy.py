from utils import fetch_ohlcv, detect_bos, detect_choch
from telegram import notify

def get_fibo_zone():
    candles_m15 = fetch_ohlcv('15m')[-70:]
    candles_h1 = fetch_ohlcv('1h')[-50:]

    trend_h1 = detect_bos(candles_h1)
    choch = detect_choch(candles_m15)

    if not choch:
        return None, trend_h1, "none"

    if choch != trend_h1 or trend_h1 is None:
        return None, trend_h1, "skip"

    highs = [c[2] for c in candles_m15]
    lows = [c[3] for c in candles_m15]
    swing_high = max(highs)
    swing_low = min(lows)

    if choch == 'bullish':
        fibo = {
            'low': swing_low,
            'high': swing_high,
            'levels': {
                '61.8': swing_low + 0.618 * (swing_high - swing_low),
                '78.6': swing_low + 0.786 * (swing_high - swing_low)
            },
            'tp': swing_high,
            'sl': swing_low,
            'direction': 'long'
        }
    else:
        fibo = {
            'low': swing_low,
            'high': swing_high,
            'levels': {
                '61.8': swing_high - 0.618 * (swing_high - swing_low),
                '78.6': swing_high - 0.786 * (swing_high - swing_low)
            },
            'tp': swing_low,
            'sl': swing_high,
            'direction': 'short'
        }

    return fibo, trend_h1, "ok"
