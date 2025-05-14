from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_message(msg):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    try:
        r = requests.post(url, data=data)
        if r.status_code != 200:
            print("Telegram ส่งไม่สำเร็จ:", r.text)
        else:
            print("ส่ง Telegram สำเร็จ:", msg)
    except Exception as e:
        print("Telegram Error:", e)
