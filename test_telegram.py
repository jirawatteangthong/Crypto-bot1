import requests

TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

def send_test_message():
    message = "Test: บอทเชื่อมต่อ Telegram สำเร็จ!"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }

    response = requests.post(url, data=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)

send_test_message()
