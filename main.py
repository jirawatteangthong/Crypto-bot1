import requests
import hmac
import hashlib
import time
import json

API_KEY = "a279dbed-ae3c-44c2-b0c4-fcf1ff6e76cb"
API_SECRET = "FA68643E5A176C00AB09637CBC5DA82E"
API_PASSPHRASE = "Jirawat1-"
BASE_URL = "https://www.okx.com"

def get_okx_timestamp():
    try:
        response = requests.get(f"{BASE_URL}/api/v5/public/time")
        timestamp = response.json()['data'][0]['ts']
        return str(float(timestamp) / 1000)  # Convert milliseconds to seconds
    except Exception as e:
        print(f"[ERROR] ไม่สามารถดึงเวลา OKX: {str(e)}")
        return str(int(time.time()))  # fallback to system time if OKX API fails

def sign(timestamp, method, request_path, body=""):
    msg = f"{timestamp}{method}{request_path}{body}"
    return hmac.new(API_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()

def get_headers(method, path, body=""):
    timestamp = get_okx_timestamp()  # Use timestamp from OKX API
    signature = sign(timestamp, method, path, body)
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

def get_balance():
    path = "/api/v5/account/balance?ccy=USDT"
    try:
        response = requests.get(BASE_URL + path, headers=get_headers("GET", path)).json()
        return float(response['data'][0]['details'][0]['availBal'])
    except Exception as e:
        print(f"[ERROR] ไม่สามารถดึง Balance: {str(e)}")
        return 0
