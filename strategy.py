from utils import fetch_ohlcv, detect_bos, detect_choch

last_bos = None

def get_fibo_zone():
    global last_bos
    candles_h1 = fetch_ohlcv('1h')
    trend = detect_bos(candles_h1)

    if trend != last_bos and trend is not None:
        last_bos = trend

    choch = detect_choch(candles_h1)
    if not choch or choch != trend:
        return None, trend, 'wait'

    high = max([c[2] for c in candles_h1])
    low = min([c[3] for c in candles_h1])

    direction = 'long' if trend == 'bullish' else 'short'

    fibo = {
        'direction': direction,
        'levels': {
            '0.0': low if direction == 'long' else high,
            '61.8': low + 0.618 * (high - low) if direction == 'long' else high - 0.618 * (high - low),
            '78.6': low + 0.786 * (high - low) if direction == 'long' else high - 0.786 * (high - low),
            '100': high if direction == 'long' else low
        },
        'tp': high - 10 if direction == 'long' else low + 10,
        'sl': low - 20 if direction == 'long' else high + 20
    }

    return fibo, trend, 'valid'
