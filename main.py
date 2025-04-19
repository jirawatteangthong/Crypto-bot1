from flask import Flask
import threading
import requests
import time
import os

app = Flask(__name__)

# ========== ตั้งค่า Telegram ==========
TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'  # แก้เป็น chat_id ของคุณ (อย่าลืมใช้แบบเป็น string)

# ========== ฟังก์ชันส่งข้อความไป Telegram ==========
def notify_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        response = requests.post(url, data=data)
        print("Telegram Response:", response.json())  # DEBUG
    except Exception as e:
        print("Telegram Error:", str(e))


# ========== ฟังก์ชันบอทรัน background ==========
def run_bot():
    notify_telegram("Bot started and running on background thread!")
    while True:
        print("บอทกำลังทำงาน... (คุณสามารถใส่ logic เทรดตรงนี้)")
        time.sleep(10)

# ========== Flask Route ==========
@app.route('/')
def home():
    return "Crypto Bot is running!"

# ========== เริ่มทำงาน ==========
if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
