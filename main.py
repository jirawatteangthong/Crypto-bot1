# main.py
from telegram import send_message

def main():
    print("เริ่มทำงานบอทเทรด...")
    send_message("✅ บอทเทรด BTC Futures (OKX) เริ่มทำงานแล้ว")

    # TODO: ส่วนหลักของบอทเทรด เช่น:
    # - ดึงข้อมูล OHLC M5
    # - ตรวจจับ BOS
    # - วาด Fibonacci
    # - เปิดออเดอร์ที่ 62% พร้อม SL/TP
    # - จำกัด 5 ไม้ต่อวัน
    # - ส่งแจ้งเตือนเมื่อเปิด/ปิดออเดอร์
    # - สรุปกำไร/ขาดทุนรายวัน

if __name__ == "__main__":
    main()
