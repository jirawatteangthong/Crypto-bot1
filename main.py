from flask import Flask
import threading
import os
import time

app = Flask(__name__)

# ตัวอย่างฟังก์ชันบอท (คุณสามารถเปลี่ยนเป็นโค้ดเทรดของคุณได้)
def run_bot():
    while True:
        print("บอททำงานอยู่...")
        # ตรงนี้ใส่โค้ดบอทเทรดจริงของคุณได้เลย เช่น ดึงราคาจาก Binance แล้วเทรด
        time.sleep(10)  # ให้รอ 10 วินาที แล้วทำงานใหม่เรื่อย ๆ

@app.route('/')
def home():
    return "Crypto Bot is running!"

if __name__ == '__main__':
    # รันบอทใน background
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # รัน Flask server ที่ Render สามารถเข้าถึงได้
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
