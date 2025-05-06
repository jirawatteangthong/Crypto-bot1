from utils import fetch_ohlcv, detect_order_blocks, detect_bos, draw_fibonacci

def get_m15_zones():
    candles = fetch_ohlcv('15m')
    trend, choch = detect_bos(candles)
    fibo = draw_fibonacci(candles, trend, choch)
    ob_zones = detect_order_blocks(candles, fibo)
    return {'ob': ob_zones, 'fibo': fibo}, trend
