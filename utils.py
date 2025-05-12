import logging
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        r = requests.post(url, data=payload)
        print(f"Telegram Response: {r.status_code} | {r.text}")
    except Exception as e:
        print(f"Telegram ERROR: {e}")

logging.basicConfig(
    filename="trading_log.txt",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def log(msg):
    logging.info(msg)
