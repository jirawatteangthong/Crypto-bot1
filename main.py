# main.py - บอทเทรด OKX (All-in + Compound + SL/TP ตามโครงสร้าง + ปรับ Leverage อัตโนมัติ)
import ccxt
import time
import pandas as pd
import numpy as np
import requests

TELEGRAM_TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
TELEGRAM_CHAT_ID = '8104629569'

okx = ccxt.okx({
    'apiKey': '0659b6f2-c86a-466a-82ec-f1a52979bc33',
    'secret': 'CCB0A67D53315671F599050FCD712CD1',
    'password': 'Jirawat1-',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

SYMBOL = 'BTC-USDT-SWAP'
LEVERAGE_CAP = 20
RR_RATIO = 2

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except:
        print("Failed to send Telegram message")

def get_balance():
    balance = okx.fetch_balance()
    return float(balance['total']['USDT'])

def get_ohlcv_safe(symbol, timeframe, limit=100):
    for _ in range(3):
        try:
            return okx.fetch_ohlcv(symbol, timeframe, limit=limit)
        except:
            time.sleep(1)
    return []

def calculate_std_band(df, std_factor=2):
    df['ma'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper'] = df['ma'] + std_factor * df['std']
    df['lower'] = df['ma'] - std_factor * df['std']
    return df

def macd(df):
    df['ema12'] = df['close'].ewm(span=12).mean()
    df['ema26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9).mean()
    return df

def get_trend_h1():
    df = pd.DataFrame(get_ohlcv_safe(SYMBOL, '1h', 50), columns=['ts','o','h','l','c','v'])
    if df.empty:
        return None
    return 'up' if df['c'].iloc[-1] > df['c'].iloc[-20] else 'down'

def get_poi_m15():
    df = pd.DataFrame(get_ohlcv_safe(SYMBOL, '15m', 50), columns=['ts','o','h','l','c','v'])
    if df.empty:
        return None
    return {'high': df['h'].max(), 'low': df['l'].min()}

def entry_signal_m1(trend, poi):
    df = pd.DataFrame(get_ohlcv_safe(SYMBOL, '1m', 100), columns=['ts','o','h','l','c','v'])
    if df.empty:
        return None
    df = df.astype(float)
    df = macd(df)
    df = calculate_std_band(df)
    last = df.iloc[-1]

    if trend == 'up' and last['macd'] > last['signal'] and last['l'] <= poi['low'] and poi['low'] >= last['lower']:
        return 'buy', last['c']
    if trend == 'down' and last['macd'] < last['signal'] and last['h'] >= poi['high'] and poi['high'] <= last['upper']:
        return 'sell', last['c']
    return None

def calculate_sl_tp(entry_price, direction, swing_sl_price):
    sl = swing_sl_price
    if direction == 'buy':
        tp = entry_price + (entry_price - sl) * RR_RATIO
    else:
        tp = entry_price - (sl - entry_price) * RR_RATIO
    return sl, tp

def calculate_leverage(entry_price, sl_price, capital):
    risk_per_unit = abs(entry_price - sl_price)
    position_size = capital / risk_per_unit
    position_value = position_size * entry_price
    leverage = min(position_value / capital, LEVERAGE_CAP)
    return round(leverage)

def open_order(direction, entry_price, sl_price, tp_price, size, leverage):
    side = 'buy' if direction == 'buy' else 'sell'
    okx.set_leverage(leverage, SYMBOL, {'marginMode': 'cross'})
    send_telegram(f"เข้าออเดอร์ {side.upper()} @ {entry_price}\nSL: {sl_price} | TP: {tp_price}")
    return okx.private_post_trade_order_algo({
        'instId': SYMBOL,
        'tdMode': 'cross',
        'side': side,
        'ordType': 'oco',
        'sz': size,
        'tpTriggerPx': str(tp_price),
        'tpOrdPx': '-1',
        'slTriggerPx': str(sl_price),
        'slOrdPx': '-1'
    })

# MAIN LOOP
while True:
    try:
        open_positions = okx.fetch_positions([SYMBOL])
        has_position = any(float(pos['contracts']) > 0 for pos in open_positions)
        if has_position:
            time.sleep(30)
            continue

        trend = get_trend_h1()
        poi = get_poi_m15()
        signal = entry_signal_m1(trend, poi)

        if signal:
            direction, entry_price = signal
            swing_price = poi['low'] if direction == 'buy' else poi['high']
            sl_price, tp_price = calculate_sl_tp(entry_price, direction, swing_price)
            capital = get_balance()
            leverage = calculate_leverage(entry_price, sl_price, capital)
            size = round((capital * leverage) / entry_price, 3)
            open_order(direction, entry_price, sl_price, tp_price, size, leverage)

    except Exception as e:
        send_telegram(f"Error: {e}")
    time.sleep(10)
