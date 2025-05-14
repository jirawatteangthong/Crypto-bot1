from utils import get_highs_lows, fetch_ohlcv

def detect_bos_and_swing(candles):
    closes = [c['close'] for c in candles]
    if closes[-1] > closes[-2] > closes[-3]:
        trend = 'bullish'
    elif closes[-1] < closes[-2] < closes[-3]:
        trend = 'bearish'
    else:
        return None, None

    highs, lows = get_highs_lows(candles[-20:])
    return trend, {'high': max(highs), 'low': min(lows)}
