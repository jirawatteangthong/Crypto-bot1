import requests
import hmac
import time
import base64
from config import SYMBOL, API_KEY, API_SECRET, API_PASSPHRASE

def fetch_candles(timeframe, limit=200):
    url = f"https://www.okx.com/api/v5/market/candles?instId={SYMBOL}&bar={timeframe}&limit={limit}"
    r = requests.get(url).json()
    return list(reversed(r['data']))

def fetch_current_price():
    candles = fetch_candles("1h", 1)
    return float(candles[-1][4])

def detect_bos_choch(candles):
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
        return len(candles) - 2, 'long'
    elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:
        return len(candles) - 2, 'short'
    return None, None

def draw_fibonacci(candles, choch_index, direction):
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]

    if direction == 'long':
        swing_low = lows[choch_index]
        swing_high = highs[-1]
        fib_levels = {
            '100': swing_low,
            '78.6': swing_low + 0.786 * (swing_high - swing_low),
            '61.8': swing_low + 0.618 * (swing_high - swing_low),
            '0': swing_high
        }
        tp = swing_high - (swing_high - swing_low) * 0.1
        sl = swing_low - (swing_high - swing_low) * 0.2

    else:
        swing_high = highs[choch_index]
        swing_low = lows[-1]
        fib_levels = {
            '100': swing_high,
            '78.6': swing_high - 0.786 * (swing_high - swing_low),
            '61.8': swing_high - 0.618 * (swing_high - swing_low),
            '0': swing_low
        }
        tp = swing_low + (swing_high - swing_low) * 0.1
        sl = swing_high + (swing_high - swing_low) * 0.2

    return {
        'direction': direction,
        'levels': fib_levels,
        'tp': round(tp, 1),
        'sl': round(sl, 1)
    }

def get_okx_balances():
    url = "https://www.okx.com/api/v5/account/balance"
    timestamp = str(time.time())
    method = "GET"
    path = "/api/v5/account/balance"
    body = ""

    msg = f"{timestamp}{method}{path}{body}"
    sign = base64.b64encode(hmac.new(API_SECRET.encode(), msg.encode(), 'sha256').digest()).decode()

    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": API_PASSPHRASE,
        "Content-Type": "application/json"
    }

    res = requests.get(url, headers=headers).json()
    coins = res.get("data", [])[0].get("details", [])
    summary = []
    for c in coins:
        total = float(c['cashBal']) + float(c.get('frozenBal', 0))
        if total > 0:
            summary.append(f"{c['ccy']}: {total:.4f}")
    return "\n".join(summary) if summary else "ไม่มีเหรียญคงเหลือในบัญชี"
