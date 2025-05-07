import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def notify(message):
    requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
        json={'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    )

def trade_notify(direction=None, entry=None, size=None, tp=None, sl=None, result=None, pnl=None, new_cap=None):
    if direction:
        notify(f"[ENTRY] {direction.upper()} @ {entry:.2f}\nSize: {size}\nTP: {tp:.2f}\nSL: {sl:.2f}")
    if result:
        notify(f"[CLOSE] {result} | PnL: {pnl:.2f} USDT\nCapital: {new_cap:.2f}")

def health_check(capital):
    notify(f"[HEALTH CHECK] BOT STATUS\nCapital: {capital:.2f} USDT")
