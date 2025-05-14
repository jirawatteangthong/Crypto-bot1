def calculate_fibonacci_levels(swing, trend):
    high, low = swing['high'], swing['low']
    diff = high - low
    if trend == 'bullish':
        entry = low + 0.618 * diff
        sl = low - 0.1 * diff
        tp = entry + (entry - sl)
        direction = 'long'
    else:
        entry = high - 0.618 * diff
        sl = high + 0.1 * diff
        tp = entry - (sl - entry)
        direction = 'short'
    return {'direction': direction, 'price': entry, 'tp': tp, 'sl': sl}
