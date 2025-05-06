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

def open_trade(signal, capital):
    direction, price = signal['direction'], signal['price']
    size = round((capital * LEVERAGE) / price, 3)
    side = 'buy' if direction == 'long' else 'sell'

    sl_price = round(signal['ob']['low'] * (1 - SL_BUFFER), 2) if direction == 'long' else round(signal['ob']['high'] * (1 + SL_BUFFER), 2)
    tp_price = round(price + (price - sl_price) * TP_RATIO, 2) if direction == 'long' else round(price - (sl_price - price) * TP_RATIO, 2)

    exchange.create_market_order(SYMBOL, side, size)

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

def monitor_trade(result, moved_sl, capital):
    orders = exchange.fetch_closed_orders(SYMBOL)
    for o in orders:
        if o['status'] == 'closed':
            pnl = float(o['info'].get('pnl', 0))
            result = "WIN" if pnl > 0 else "LOSS"
            capital += pnl
            trade_notify(result=result, pnl=pnl, new_cap=capital)
            break
