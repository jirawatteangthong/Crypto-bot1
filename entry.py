from utils import fetch_ohlcv, detect_bos, detect_choch

def get_fibo_zone():
    candles_h1 = fetch_ohlcv('1h')[-200:]  # ใช้ 200 แท่ง
    candles_m15 = fetch_ohlcv('15m')[-200:]

    trend = detect_bos(candles_h1)
    choch = detect_choch(candles_m15)

    if not trend or not choch:
        return None, trend, 'skip'

    # เทรนด์ขาขึ้น → วาดจาก low=100 ไป high=0
    if trend == 'bullish' and choch == 'bullish':
        swing_low = min([c[3] for c in candles_h1[-70:]])
        swing_high = max([c[2] for c in candles_h1[-70:]])
        fibo_100 = swing_low
        fibo_0 = swing_high
        direction = 'long'

        sl = fibo_100 - (fibo_0 - fibo_100) * 0.1   # SL ต่ำกว่า Fibo 100
        tp = fibo_0 + (fibo_0 - fibo_100) * 0.1      # TP ก่อนถึง Fibo 0

    # เทรนด์ขาลง → วาดจาก high=100 ไป low=0
    elif trend == 'bearish' and choch == 'bearish':
        swing_high = max([c[2] for c in candles_h1[-70:]])
        swing_low = min([c[3] for c in candles_h1[-70:]])
        fibo_100 = swing_high
        fibo_0 = swing_low
        direction = 'short'

        sl = fibo_100 + (fibo_100 - fibo_0) * 0.1   # SL สูงกว่า Fibo 100
        tp = fibo_0 - (fibo_100 - fibo_0) * 0.1      # TP ก่อนถึง Fibo 0

    else:
        return None, trend, 'skip'

    # คำนวณระดับ 61.8 และ 78.6
    levels = {
        '61.8': fibo_100 - (fibo_100 - fibo_0) * 0.618,
        '78.6': fibo_100 - (fibo_100 - fibo_0) * 0.786
    }

    return {
        'direction': direction,
        'levels': levels,
        'tp': round(tp, 2),
        'sl': round(sl, 2)
    }, trend, 'ok'
