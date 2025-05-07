import ccxt
from config import *
from telegram import trade_notify
from utils import exchange

current_order_id = None

def open_trade(signal, capital):
    global current_order_id
    direction, price = signal['direction'], signal['price']
    size = round((capital * LEVERAGE) / price, 3)
    side = 'buy' if direction == 'long' else 'sell'

    sl_price = round(signal['ob']['low'] * (1 - SL_BUFFER), 2) if direction == 'long' else round(signal['ob']['high'] * (1 + SL_BUFFER), 2)
    tp_price = round(price + (price - sl_price) * TP_RATIO, 2) if direction == 'long' else round(price - (sl_price - price) * TP_RATIO, 2)

    order = exchange.create_market_order(SYMBOL, side, size)
    current_order_id = order['id']

    # TP/SL (OCO)
    exchange.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': 'sell' if side == 'buy' else 'buy',
        'ordType': 'oco',
        'sz': size,
        'tpTriggerPx': tp_price,
        'tpOrdPx': '-1',
        'slTriggerPx': sl_price,
        'slOrdPx': '-1'
    })

    trade_notify(direction, price, size, tp_price, sl_price)
    return capital, "pending", False

def monitor_trade():
    global current_order_id
    if not current_order_id:
        return
    orders = exchange.fetch_closed_orders(SYMBOL)
    for o in orders:
        if o['id'] == current_order_id and o['status'] == 'closed':
            pnl = float(o['info'].get('pnl', 0))
            result = "WIN" if pnl > 0 else "LOSS"
            new_cap = pnl + START_CAPITAL
            trade_notify(result=result, pnl=pnl, new_cap=new_cap)
            current_order_id = None
            break

def has_any_order():
    positions = exchange.fetch_positions([SYMBOL])
    for p in positions:
        if float(p['contracts']) > 0:
            return True
    return False
