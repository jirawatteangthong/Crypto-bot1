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
    size = size if signal['full_size'] else size / 2
    side = 'buy' if direction == 'long' else 'sell'

    sl_price = round(signal['ob']['low'] * (1 - SL_BUFFER), 2) if direction == 'long' else round(signal['ob']['high'] * (1 + SL_BUFFER), 2)
    tp_price = round(price + (price - sl_price) * TP_RATIO, 2) if direction == 'long' else round(price - (sl_price - price) * TP_RATIO, 2)

    exchange.create_limit_order(SYMBOL, side, size, price)

    trade_notify(direction, price, size, tp_price, sl_price)
    return capital, "pending", False

def monitor_trade(result, moved_sl, capital):
    orders = exchange.fetch_closed_orders(SYMBOL, limit=5)
    for o in orders:
        if o['status'] == 'closed' and float(o['amount']) > 0:
            entry_price = float(o['price']) or float(o['info'].get('fillPx', 0))
            exit_price = float(o['average']) or float(o['info'].get('avgPx', 0))
            size = float(o['amount'])

            if entry_price == 0 or exit_price == 0:
                continue  # ข้ามถ้ายังไม่มีข้อมูลที่ต้องการ

            if o['side'] == 'buy':
                pnl = (exit_price - entry_price) * size
            else:
                pnl = (entry_price - exit_price) * size

            result = "WIN" if pnl > 0 else "LOSS"
            capital += pnl
            trade_notify(result=result, pnl=pnl, new_cap=capital)
            break
