from utils import fetch_ohlcv, detect_bos, detect_choch
from telegram import notify

last_h1_bos = None
last_h1_swing = {}

def get_fibo_zone():
    global last_h1_bos, last_h1_swing

    candles_h1 = fetch_ohlcv('1h')[-50:]
    candles_m15 = fetch_ohlcv('15m')[-70:]

    trend_h1 = detect_bos(candles_h1)

    if trend_h1 and trend_h1 != last_h1_bos:
        highs = [c[2] for c in candles_h1[-20:]]
        lows = [c[3] for c in candles_h1[-20:]]
        if trend_h1 == 'bullish':
            swing_high = max(highs)
            swing_low = min(lows)
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
            swing_high = max(highs)
            swing_low = min(lows)
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
        last_h1_bos = trend_h1
        last_h1_swing = fibo
        notify(f"[H1 BOS] à¹à¸à¸§à¹à¸à¹à¸¡ {trend_h1} â à¸§à¸²à¸ Fibo à¹à¸«à¸¡à¹")

    if not last_h1_swing:
        return None, trend_h1, 'wait'

    choch = detect_choch(candles_m15)
    if choch == last_h1_bos:
        return last_h1_swing, trend_h1, 'ok'
    else:
        return None, trend_h1, 'wait'
