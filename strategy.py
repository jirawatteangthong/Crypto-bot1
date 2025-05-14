def detect_bos(candles):
    # ใช้เงื่อนไข simple: high หรือ low ทะลุ swing เดิม
    last = candles[-1]
    prev = candles[-2]

    if last['high'] > prev['high']:
        return 'up'
    elif last['low'] < prev['low']:
        return 'down'
    return None

def get_fibonacci(swing_high, swing_low):
    fib_62 = swing_low + (swing_high - swing_low) * 0.62
    fib_110 = swing_low + (swing_high - swing_low) * 1.1
    return fib_62, fib_110
