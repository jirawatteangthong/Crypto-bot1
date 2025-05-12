import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from utils import get_okx_balances

def notify(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def health_check(capital):
    balances = get_okx_balances()
    notify(f"[HEALTH CHECK]\nCapital: ${capital:.2f}\n\n[บัญชี OKX]\n{balances}")
