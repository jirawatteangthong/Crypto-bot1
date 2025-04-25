import time
import hmac
import hashlib
import json
import requests

# ====== OKX API Configuration ======
OKX_API_KEY = "0659b6f2-c86a-466a-82ec-f1a52979bc33"
OKX_API_SECRET = "CCB0A67D53315671F599050FCD712CD1"
OKX_API_PASSPHRASE = "Jirawat1-"

# ====== Trading Settings ======
SYMBOL = "BTC-USDT-SWAP"
START_CAPITAL = 20
LEVERAGE = 10
TP_RATIO = 2.0               # TP = 2 เท่าของความเสี่ยง
SL_BUFFER = 0.0015           # เผื่อ SL 0.15%
BE_TRIGGER_RATIO = 0.5       # ขยับ SL ไป BE เมื่อได้กำไร 50% ของ TP

# ====== Telegram Configuration ======
TELEGRAM_TOKEN = "7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY"
TELEGRAM_CHAT_ID = "8104629569"

capital = START_CAPITAL
tp_streak = 0
current_order = None

# ====== OKX API Client ======
class OKXClient:
    def __init__(self):
        self.api_key = OKX_API_KEY
        self.secret_key = OKX_API_SECRET
        self.passphrase = OKX_API_PASSPHRASE

    def _generate_signature(self, method, endpoint, params):
        timestamp = str(time.time())
        body = json.dumps(params) if params else ''
        message = timestamp + method.upper() + endpoint + body
        signature = hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature, timestamp

    def place_order(self, symbol, side, entry_price, sl, tp, size):
        url = f"https://www.okx.com/api/v5/trade/order"
        params = {
            "instId": symbol,
            "tdMode": "cross",
            "side": side,
            "ordType": "limit",
            "px": entry_price,
            "sz": size,
            "sl": sl,
            "tp": tp
        }
        signature, timestamp = self._generate_signature("POST", "/api/v5/trade/order", params)
        headers = {
            "OK-API-API-KEY": self.api_key,
            "OK-API-PASSPHRASE": self.passphrase,
            "OK-API-TIMESTAMP": timestamp,
            "OK-API-SIGN": signature
        }
        response = requests.post(url, json=params, headers=headers)
        return response.json()

    def check_order_status(self, order_id):
        url = f"https://www.okx.com/api/v5/trade/order/{order_id}"
        signature, timestamp = self._generate_signature("GET", f"/api/v5/trade/order/{order_id}", None)
        headers = {
            "OK-API-API-KEY": self.api_key,
            "OK-API-PASSPHRASE": self.passphrase,
            "OK-API-TIMESTAMP": timestamp,
            "OK-API-SIGN": signature
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def calculate_pnl(self, order):
        # พิจารณากำไรขาดทุนจากออเดอร์
        return {"pnl": 10}  # ตัวอย่างการคำนวณกำไร

# ====== Telegram Alert ======
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=payload)
    return response.json()

# ====== Strategy — Signal Generator ======
def get_trade_signal():
    # วิเคราะห์สัญญาณการเทรด (ตัวอย่าง)
    return {
        "side": "long",
        "entry": 50000,
        "sl": 49000,
        "tp": 52000
    }

# ====== Main Loop ======
try:
    send_telegram_alert("วัยรุ่น_บอทเริ่มทำงานแล้ว!")

    while True:
        if current_order:
            status = okx.check_order_status(current_order["order_id"])
            if status["data"][0]["state"] == "filled":
                result = okx.calculate_pnl(current_order)
                pnl = result["pnl"]
                capital += pnl

                msg = f'ปิดออเดอร์แล้ว\\nผลลัพธ์: {"กำไร" if pnl > 0 else "ขาดทุน"} {pnl:.2f} USDT\\nทุนปัจจุบัน: {capital:.2f} USDT'
                send_telegram_alert(msg)

                if pnl > 0:
                    tp_streak += 1
                    if tp_streak >= 3:
                        withdraw_amt = capital / 2
                        capital -= withdraw_amt
                        send_telegram_alert(f"🏦 TP ติดกัน 3 ครั้ง!\\nพิจารณาถอนกำไร: {withdraw_amt:.2f} USDT")
                        tp_streak = 0
                else:
                    tp_streak = 0

                current_order = None

        if not current_order:
            signal = get_trade_signal()
            if signal:
                entry = signal["entry"]
                sl = signal["sl"] * (1 - SL_BUFFER if signal["side"] == "long" else 1 + SL_BUFFER)
                tp = entry + ((entry - sl) * TP_RATIO if signal["side"] == "long" else -((sl - entry) * TP_RATIO))
                position_size = (capital * LEVERAGE) / entry

                order = okx.place_order(
                    symbol=SYMBOL,
                    side=signal["side"],
                    entry_price=entry,
                    sl=sl,
                    tp=tp,
                    size=position_size
                )

                current_order = {
                    "order_id": order["data"]["ordId"],
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "side": signal["side"],
                    "size": position_size
                }

                send_telegram_alert(
                    f"เปิดออเดอร์ใหม่: {signal['side'].upper()}\\nEntry: {entry:.2f}\\nSL: {sl:.2f}\\nTP: {tp:.2f}\\nขนาด: {position_size:.4f} BTC"
                )

        time.sleep(20)

except KeyboardInterrupt:
    send_telegram_alert("⛔️ หยุดบอทด้วยมือ")
except Exception as e:
    send_telegram_alert(f"⚠️ บอทผิดพลาด: {str(e)}")
