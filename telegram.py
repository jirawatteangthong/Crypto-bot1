import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_message(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    try:
        requests.post(url, data=data)
    except:
        print("Telegram Error")
