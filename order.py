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

open_order_ids = []

def open_trade(signal, capital):
    side = 'buy' if signal['direction'] == 'long' else 'sell'
    order = exchange.create_limit_order(SYMBOL, side, ORDER_SIZE, signal['price'])
    open_order_ids.append(order['id'])

    trade_notify(direction=signal['direction'], entry=signal['price'],
                 size=ORDER_SIZE, tp=signal['tp'], sl=signal['sl'])
    return capital

def monitor_trades(capital):
    global open_order_ids
    for order_id in open_order_ids[:]:
        try:
            o = exchange.fetch_order(order_id, SYMBOL)
            if o['status'] == 'closed':
                pnl = float(o['info'].get('pnl', 0))
                result = "WIN" if pnl > 0 else "LOSS"
                capital += pnl
                trade_notify(result=result, pnl=pnl, new_cap=capital)
                open_order_ids.remove(order_id)
        except:
            continue
    return open_order_ids, capital
