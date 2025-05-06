from utils import fetch_ohlcv, detect_bos

def get_fibo_zone_from_bos():
    candles = fetch_ohlcv('1h')
    bos_list = detect_bos(candles)

    if not bos_list:
        return None

    last_bos = bos_list[-1]
    swing_high = last_bos['high']
    swing_low = last_bos['low']

    if last_bos['type'] == 'bullish':
        fibo_618 = swing_high - (swing_high - swing_low) * 0.618
        fibo_786 = swing_high - (swing_high - swing_low) * 0.786
    else:
        fibo_618 = swing_low + (swing_high - swing_low) * 0.618
        fibo_786 = swing_low + (swing_high - swing_low) * 0.786

    return {
        'direction': 'long' if last_bos['type'] == 'bullish' else 'short',
        'low': min(fibo_618, fibo_786),
        'high': max(fibo_618, fibo_786),
        'swing': {'high': swing_high, 'low': swing_low}
    }
