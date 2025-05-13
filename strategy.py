from utils import fetch_ohlcv, detect_bos, detect_choch
from telegram import notify

def get_fibo_zone():
    candles_h1 = fetch_ohlcv('1h')[-200:]
    
    trend_h1 = detect_bos(candles_h1)
    choch = detect_choch(candles_h1)

    if not trend_h1:
        return None, None, 'wait'

    if not choch:
        return None, trend_h1, 'wait'

    if choch != trend_h1:
        return None, trend_h1, 'skip'

    highs = [c[2] for c in candles_h1]
    lows = [c[3] for c in candles_h1]
    swing_high = max(highs[-70:])
    swing_low = min(lows[-70:])

    if trend_h1 == 'bullish':
        fibo = {
            'low': swing_low,
            'high': swing_high,
            'levels': {
                '61.8': swing_low + 0.618 * (swing_high - swing_low),
                '78.6': swing_low + 0.786 * (swing_high - swing_low)
            },
            'tp': swing_high - 10,  # TP slightly before high
            'sl': swing_high + 20,  # SL slightly above high
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
            'tp': swing_low + 10,  # TP slightly before low
            'sl': swing_low - 20,  # SL slightly below low
            'direction': 'short'
        }

    return fibo, trend_h1, 'ok'
