import ccxt
from config import *
from telegram import trade_notify

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

latest_order_id = None
entry_price = None

def open_trade(signal, capital):
    global latest_order_id, entry_price
    direction, price = signal['direction'], signal['price']
    portion = 1.0 if not signal['ob'].get('partial') else 0.5
    size = round((capital * LEVERAGE * portion) / price, 3)
    side = 'buy' if direction == 'long' else 'sell'

    sl_price = round(signal['ob']['low'] * (1 - SL_BUFFER), 2) if direction == 'long' else round(signal['ob']['high'] * (1 + SL_BUFFER), 2)
    tp_price = round(price + (price - sl_price) * TP_RATIO, 2) if direction == 'long' else round(price - (sl_price - price) * TP_RATIO, 2)

    order = exchange.create_limit_order(SYMBOL, side, size, price)
    latest_order_id = order['id']
    entry_price = price

    # TP/SL OCO
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
    global latest_order_id, entry_price
    if not latest_order_id: return
    orders = exchange.fetch_closed_orders(SYMBOL)
    for o in orders:
        if o['id'] == latest_order_id and o['status'] == 'closed':
            close_price = float(o.get('average', entry_price))
            pnl = (close_price - entry_price) if o['side'] == 'buy' else (entry_price - close_price)
            result = "WIN" if pnl > 0 else "LOSS"
            trade_notify(result=result, pnl=pnl, new_cap=CAPITAL + pnl)
            latest_order_id = None
