from utils import fetch_ohlcv, detect_bos, detect_choch
from telegram import notify

last_fibo = {'high': None, 'low': None, 'direction': None}

def get_fibo_zone():
    global last_fibo
    candles_h1 = fetch_ohlcv('1h')[-200:]
    candles_m15 = fetch_ohlcv('15m')[-70:]

    trend = detect_bos(candles_h1)
    choch_m15 = detect_choch(candles_m15)

    if not trend or not choch_m15 or choch_m15 != trend:
        return None, trend, 'wait'

    highs = [c[2] for c in candles_h1[-70:]]
    lows = [c[3] for c in candles_h1[-70:]]

    high = max(highs)
    low = min(lows)

    if last_fibo['high'] and last_fibo['low']:
        fib_range = abs(last_fibo['high'] - last_fibo['low'])
        retracement = abs(candles_h1[-1][4] - last_fibo['low']) / fib_range * 100 if trend == 'bullish' else abs(candles_h1[-1][4] - last_fibo['high']) / fib_range * 100
        if retracement < 33.33:
            if trend == 'bullish' and high > last_fibo['high']:
                last_fibo['high'] = high
            elif trend == 'bearish' and low < last_fibo['low']:
                last_fibo['low'] = low
        else:
            if trend == 'bullish':
                last_fibo['low'] = low
                last_fibo['high'] = high
            else:
                last_fibo['high'] = high
                last_fibo['low'] = low
    else:
        last_fibo['high'] = high
        last_fibo['low'] = low
        last_fibo['direction'] = trend

    notify(f"[NEW FIBO] Direction: {trend.upper()}\nLow={last_fibo['low']}\nHigh={last_fibo['high']}")

    if trend == 'bullish':
        fibo = {
            'direction': 'long',
            'levels': {
                '61.8': last_fibo['low'] + 0.618 * (last_fibo['high'] - last_fibo['low']),
                '78.6': last_fibo['low'] + 0.786 * (last_fibo['high'] - last_fibo['low'])
            },
            'tp': last_fibo['high'] - 10,
            'sl': last_fibo['low'] - 10
        }
    else:
        fibo = {
            'direction': 'short',
            'levels': {
                '61.8': last_fibo['high'] - 0.618 * (last_fibo['high'] - last_fibo['low']),
                '78.6': last_fibo['high'] - 0.786 * (last_fibo['high'] - last_fibo['low'])
            },
            'tp': last_fibo['low'] + 10,
            'sl': last_fibo['high'] + 10
        }

    return fibo, trend, 'ok'
