from utils import fetch_candles, detect_bos_choch, draw_fibonacci

def get_fibo_zone():
    candles = fetch_candles("1h", 200)
    choch_index, direction = detect_bos_choch(candles)

    if choch_index is None:
        return None, None, 'wait'

    fibo = draw_fibonacci(candles, choch_index, direction)
    return fibo, direction, 'ok'
