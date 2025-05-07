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

position_open = False

def open_trade(signal, capital):
    global position_open
    if position_open:
        return capital, position_open

    direction, price, ob = signal['direction'], signal['price'], signal['ob']
    side = 'buy' if direction == 'long' else 'sell'
    size = ORDER_SIZE

    sl_price = ob['low'] if direction == 'long' else ob['high']
    tp_price = ob['high'] if direction == 'long' else ob['low']

    exchange.create_limit_order(SYMBOL, side, size, price)

    trade_notify(direction, price, size, tp_price, sl_price)
    position_open = True
    return capital, position_open

def monitor_trade(capital):
    global position_open
    orders = exchange.fetch_closed_orders(SYMBOL)
    for o in orders:
        if o['status'] == 'closed':
            pnl = float(o['info'].get('pnl', 0))
            result = "WIN" if pnl > 0 else "LOSS"
            capital += pnl
            trade_notify(result=result, pnl=pnl, new_cap=capital)
            position_open = False
            break
    return position_open
