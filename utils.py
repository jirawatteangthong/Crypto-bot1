import logging
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Telegram API error:", response.status_code, response.text)
        else:
            print("Telegram message sent:", message)
    except Exception as e:
        print("Telegram send error:", str(e))

# Logger
logging.basicConfig(
    filename="trading_log.txt",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def log(msg):
    logging.info(msg)
