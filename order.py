from utils import exchange, fetch_current_price
from config import SYMBOL, ORDER_SIZE

open_order = None

def open_position(entry, direction, tp, sl):
    global open_order
    side = 'buy' if direction == 'long' else 'sell'
    order = exchange.create_order(SYMBOL, 'market', side, ORDER_SIZE, None)
    open_order = {
        'entry': fetch_current_price(),
        'direction': direction,
        'tp': tp,
        'sl': sl,
        'active': True
    }
    return open_order

def close_position():
    global open_order
    if not open_order or not open_order['active']:
        return None

    price = fetch_current_price()
    result = None
    pnl = 0

    if open_order['direction'] == 'long':
        if price >= open_order['tp']:
            result = 'TP'
        elif price <= open_order['sl']:
            result = 'SL'
    elif open_order['direction'] == 'short':
        if price <= open_order['tp']:
            result = 'TP'
        elif price >= open_order['sl']:
            result = 'SL'

    if result:
        entry = open_order['entry']
        exit_price = open_order['tp'] if result == 'TP' else open_order['sl']
        pnl = (exit_price - entry) * ORDER_SIZE if open_order['direction'] == 'long' else (entry - exit_price) * ORDER_SIZE
        open_order['active'] = False
        return result, pnl

    return None

def check_and_update_sl():
    global open_order
    if not open_order or not open_order['active']:
        return False

    current_price = fetch_current_price()
    entry = open_order['entry']
    tp = open_order['tp']
    sl = open_order['sl']
    direction = open_order['direction']

    # ราคาถึงครึ่งทาง TP หรือยัง
    mid_tp = (entry + tp) / 2
    if direction == 'long' and current_price >= mid_tp and sl != entry:
        open_order['sl'] = entry
        return True
    elif direction == 'short' and current_price <= mid_tp and sl != entry:
        open_order['sl'] = entry
        return True

    return False
