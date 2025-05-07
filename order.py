from config import *
from telegram import trade_notify
import ccxt

exchange = ccxt.okx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

open_positions = []

def open_trade(signal, capital):
    direction = signal['direction']
    price = signal['entry_price']
    size = 0.5
    tp = signal['tp']
    sl = signal['sl']
    side = 'buy' if direction == 'long' else 'sell'

    exchange.create_limit_order(SYMBOL, side, size, price)
    # จำลอง TP/SL ด้วยการ monitor ภายหลัง
    open_positions.append({'price': price, 'tp': tp, 'sl': sl, 'side': side, 'size': size})

    trade_notify(direction, price, size, tp, sl)
    return capital

def monitor_trades(capital):
    global open_positions
    closed = []

    for pos in open_positions:
        ticker = exchange.fetch_ticker(SYMBOL)
        current_price = ticker['last']
        win = False
        loss = False

        if pos['side'] == 'buy':
            win = current_price >= pos['tp']
            loss = current_price <= pos['sl']
        else:
            win = current_price <= pos['tp']
            loss = current_price >= pos['sl']

        if win or loss:
            pnl = (pos['tp'] - pos['price']) * pos['size'] if win else (pos['sl'] - pos['price']) * pos['size']
            pnl = pnl if pos['side'] == 'buy' else -pnl
            capital += pnl
            trade_notify(result="WIN" if win else "LOSS", pnl=pnl, new_cap=capital)
            closed.append(pos)

    open_positions = [pos for pos in open_positions if pos not in closed]
    return capital
