import time
import json
import hmac
import hashlib
import requests

# OKX API Configuration
OKX_API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
OKX_API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
OKX_API_PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"

# Telegram Configuration
TELEGRAM_API_URL = "https://api.telegram.org/bot7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY/sendMessage"
CHAT_ID = "8104629569"

# Function to send Telegram message
def send_telegram_message(message):
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(TELEGRAM_API_URL, data=payload)
        response.raise_for_status()
        print(f"Telegram message sent: {message}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] ไม่สามารถส่งข้อความไปยัง Telegram: {e}")

# Function to generate signature for OKX API requests
def generate_signature(timestamp, method, request_path, body=""):
    body = json.dumps(body) if body else ""
    sign = timestamp + method + request_path + body
    return hmac.new(OKX_API_SECRET.encode(), sign.encode(), hashlib.sha256).hexdigest()

# Function to get request headers
def get_headers(method, request_path, body=""):
    timestamp = str(time.time())
    signature = generate_signature(timestamp, method, request_path, body)
    return {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": OKX_API_PASSPHRASE,
        "Content-Type": "application/json"
    }

# Function to check the balance
def check_balance():
    path = "/api/v5/account/balance"
    headers = get_headers("GET", path)
    try:
        response = requests.get(BASE_URL + path, headers=headers).json()
        if 'code' in response and response['code'] == '0':
            usdt_balance = next((item for item in response['data'][0]['details'] if item['currency'] == 'USDT'), None)
            if usdt_balance:
                return float(usdt_balance['availBalance'])
            else:
                print("[ERROR] ไม่พบ USDT ในบัญชี")
                send_telegram_message("[ERROR] ไม่พบ USDT ในบัญชี")
        else:
            print(f"[ERROR] {response}")
    except Exception as e:
        print(f"[ERROR] เกิดข้อผิดพลาดในการดึง Balance: {str(e)}")
        send_telegram_message(f"[ERROR] เกิดข้อผิดพลาดในการดึง Balance: {str(e)}")
    return 0.0

# Function to place an order
def place_order(symbol, side, size, price):
    path = "/api/v5/trade/order"
    order_data = {
        "instId": symbol,
        "tdMode": "cross",
        "side": side,
        "ordType": "limit",
        "px": price,
        "sz": size,
        "posSide": "long" if side == "buy" else "short",
        "clOrdId": "order" + str(int(time.time() * 1000))
    }
    headers = get_headers("POST", path, json.dumps(order_data))

    try:
        response = requests.post(BASE_URL + path, headers=headers, json=order_data).json()
        if 'code' in response and response['code'] == '0':
            order_id = response['data'][0]['ordId']
            message = f"เปิดออเดอร์ {side} {symbol} ขนาด {size} ที่ราคา {price} สำเร็จ (Order ID: {order_id})"
            send_telegram_message(message)
            print(f"[ORDER] {message}")
            return order_id
        else:
            message = f"[ERROR] ไม่สามารถเปิดออเดอร์ {side} {symbol} ขนาด {size} ที่ราคา {price}"
            send_telegram_message(message)
            print(f"[ERROR] {response}")
    except Exception as e:
        print(f"[ERROR] เกิดข้อผิดพลาดในการเปิดออเดอร์: {str(e)}")
        send_telegram_message(f"[ERROR] เกิดข้อผิดพลาดในการเปิดออเดอร์: {str(e)}")

# Example usage of the functions
if __name__ == "__main__":
    # Check balance
    usdt_balance = check_balance()
    if usdt_balance > 0:
        print(f"[INFO] Balance: {usdt_balance} USDT")

        # Place an order if balance is sufficient
        symbol = "BTC-USDT-SWAP"
        side = "buy"  # or "sell"
        size = 0.01
        price = 50000  # Example price, you can adjust it
        place_order(symbol, side, size, price)
    else:
        print("[ERROR] Balance not sufficient")
