from utils import fetch_ohlcv, detect_order_blocks, detect_bos, draw_fibo

def get_m15_zones():
    candles = fetch_ohlcv('15m')
    trend, swing = detect_bos(candles)
    fibo_zone = draw_fibo(swing, trend)
    ob_zones = detect_order_blocks(candles, swing, trend)
    return {'fibo': fibo_zone, 'ob': ob_zones, 'swing': swing}, trend
