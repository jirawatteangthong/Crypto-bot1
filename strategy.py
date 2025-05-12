def detect_bos_choc(candles):
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    closes = [c['close'] for c in candles]

    bos = False
    choc = False
    trend = ''
    swing = {}

    if highs[-1] > highs[-2] and closes[-1] > highs[-2]:
        bos = True
        trend = 'up'
    elif lows[-1] < lows[-2] and closes[-1] < lows[-2]:
        bos = True
        trend = 'down'

    if trend == 'up' and closes[-1] < lows[-3]:
        choc = True
    elif trend == 'down' and closes[-1] > highs[-3]:
        choc = True

    swing = {
        'high': max(highs[-20:]),
        'low': min(lows[-20:])
    }

    return bos, choc, trend, swing

def get_fibo_zone(trend, swing):
    if trend == 'up':
        fibo_618 = swing['low'] + (swing['high'] - swing['low']) * 0.618
        fibo_786 = swing['low'] + (swing['high'] - swing['low']) * 0.786
        tp = swing['high'] - (swing['high'] - swing['low']) * 0.01
        sl = swing['low'] - (swing['high'] - swing['low']) * 0.1
    else:
        fibo_618 = swing['high'] - (swing['high'] - swing['low']) * 0.618
        fibo_786 = swing['high'] - (swing['high'] - swing['low']) * 0.786
        tp = swing['low'] + (swing['high'] - swing['low']) * 0.01
        sl = swing['high'] + (swing['high'] - swing['low']) * 0.1

    return fibo_618, fibo_786, tp, sl
