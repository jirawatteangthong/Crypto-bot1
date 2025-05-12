from telegram import notify
from config import ORDER_SIZE
from utils import fetch_current_price

def open_trade(signal, capital):
    notify(f"[ENTRY] {signal['direction'].upper()} @ {signal['price']}\nSize: {ORDER_SIZE}\nTP: {signal['tp']}\nSL: {signal['sl']}")
    return capital

def monitor_trades(positions, capital):
    return positions, capital
