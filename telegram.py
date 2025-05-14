import requests

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# Flags to ensure one-time notifications
notified_flags = {
    'bot_started': False,
    'choch_m15': False,
    'draw_fibo': False,
    'enter_zone': False,
    'error': False
}

def reset_flags():
    for key in notified_flags:
        notified_flags[key] = False

def notify_once(tag, message):
    if not notified_flags.get(tag):
        notify(message)
        notified_flags[tag] = True

def notify(message):
    requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
        json={'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    )

def trade_notify(direction=None, entry=None, size=None, tp=None, sl=None, result=None, pnl=None, new_cap=None):
    if direction:
        notify(f"[ENTRY] {direction.upper()} @ {entry}\nSize: {size}\nTP: {tp}\nSL: {sl}")
    if result:
        notify(f"[CLOSE] {result} | PnL: {pnl:.2f} USDT\nCapital: {new_cap:.2f}")

def health_check(capital):
    notify(f"[HEALTH CHECK] BOT ALIVE\nCapital: {capital:.2f} USDT")
