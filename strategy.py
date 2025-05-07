from utils import fetch_ohlcv, detect_choch, detect_bos

def get_fibo_zone():
    candles_m15 = fetch_ohlcv('15m')[-70:]
    candles_h1 = fetch_ohlcv('1h')[-50:]
    trend_h1 = detect_bos(candles_h1)  # ใช้ BOS จาก H1

    choch = detect_choch(candles_m15)
    if not choch or choch != trend_h1:
        return None, None  # ถ้า M15 ไม่สอดคล้องกับ H1 → ไม่วาด Fibo

    highs = [c[2] for c in candles_m15]
    lows = [c[3] for c in candles_m15]

    if choch == 'bullish':
        fibo_high = max(highs)
        fibo_low = min(lows)
        return {
            'trend': 'bullish',
            '61.8': fibo_low + (fibo_high - fibo_low) * 0.618,
            '78.6': fibo_low + (fibo_high - fibo_low) * 0.786,
            'tp': fibo_high,
            'sl': fibo_low
        }, 'bullish'
    else:
        fibo_high = max(highs)
        fibo_low = min(lows)
        return {
            'trend': 'bearish',
            '61.8': fibo_high - (fibo_high - fibo_low) * 0.618,
            '78.6': fibo_high - (fibo_high - fibo_low) * 0.786,
            'tp': fibo_low,
            'sl': fibo_high
        }, 'bearish'
