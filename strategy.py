def detect_bos_choc(candles):
    trend, bos, choc, swing = None, False, False, {}

    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]

    if highs[-1] > max(highs[-10:-1]):
        trend = 'up'
        bos = True
    elif lows[-1] < min(lows[-10:-1]):
        trend = 'down'
        bos = True

    if trend == 'up' and lows[-1] < lows[-5]:
        choc = True
        swing = {'low': lows[-5], 'high': highs[-1]}
    elif trend == 'down' and highs[-1] > highs[-5]:
        choc = True
        swing = {'high': highs[-5], 'low': lows[-1]}

    return bos, choc, trend, swing

def get_fibo_zone(trend, swing):
    if trend == 'up':
        fibo_618 = swing['low'] + 0.618 * (swing['high'] - swing['low'])
        fibo_786 = swing['low'] + 0.786 * (swing['high'] - swing['low'])
        tp = swing['high'] - 0.01 * (swing['high'] - swing['low'])
        sl = swing['low'] - 0.1 * (swing['high'] - swing['low'])
    else:
        fibo_618 = swing['high'] - 0.618 * (swing['high'] - swing['low'])
        fibo_786 = swing['high'] - 0.786 * (swing['high'] - swing['low'])
        tp = swing['low'] + 0.01 * (swing['high'] - swing['low'])
        sl = swing['high'] + 0.1 * (swing['high'] - swing['low'])
    return fibo_618, fibo_786, tp, sl
