import time
import requests
import json
from datetime import datetime
import numpy as np
import pytz
import talib
import schedule
import threading
from flask import Flask, request
import telegram
from okx.client import Client

# OKX API Configuration
api_key = 'e8e/82c5a-6ccd-4cb3-92a9-3f10144ecd28'
api_secret = '3E0BDFF2AF2EF11217C2DCC7E88400C3'
passphrase = 'Jirawat1-'

# Telegram Bot Configuration
telegram_token = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
chat_id = '8104629569'
bot = telegram.Bot(token=telegram_token)

# Initialize Flask app
app = Flask(__name__)

# OKX client
client = Client(api_key, api_secret, passphrase)

# Define the symbol and leverage
symbol = 'BTC-USDT-SWAP'
leverage = 10
portfolio_percentage = 0.30

# Define a function to get the current price
def get_current_price(symbol):
    response = client.get_market_ticker(symbol)
    return float(response['data'][0]['last'])

# Define a function to get the balance
def get_balance():
    response = client.get_account_balance()
    balance = response['data'][0]['equity']
    return float(balance)

# Function to check market structure (1D, H1)
def check_market_structure():
    # Fetch data for 1D and H1 timeframes
    one_day_data = client.get_market_candles(symbol, granularity=86400, limit=100)  # 1D candles
    one_hour_data = client.get_market_candles(symbol, granularity=3600, limit=100)  # 1H candles

    # Analyze market structure: HH/LL, swing high/low
    one_day_closes = [float(data[4]) for data in one_day_data]
    one_hour_closes = [float(data[4]) for data in one_hour_data]

    # Identify trend: Higher High / Higher Low or Lower Low / Lower High
    hh_ll_1d = "Bullish" if one_day_closes[-1] > one_day_closes[-2] else "Bearish"
    hh_ll_1h = "Bullish" if one_hour_closes[-1] > one_hour_closes[-2] else "Bearish"

    return hh_ll_1d, hh_ll_1h

# Function to send messages to Telegram
def send_telegram_message(message):
    bot.send_message(chat_id=chat_id, text=message)

# Function to execute trade
def execute_trade(entry_price, stop_loss, take_profit):
    balance = get_balance()
    trade_amount = balance * portfolio_percentage / entry_price  # Use 30% of the portfolio

    # Create order
    order = client.place_order(
        symbol=symbol,
        side="buy",  # or "sell" based on trend
        ord_type="market",
        size=trade_amount,
        leverage=leverage
    )

    # Send message to Telegram
    send_telegram_message(f"Trade executed at {entry_price}. SL: {stop_loss}, TP: {take_profit}")

    # Set stop loss and take profit
    client.set_stop_loss(symbol=symbol, stop_loss=stop_loss, order_id=order['order_id'])
    client.set_take_profit(symbol=symbol, take_profit=take_profit, order_id=order['order_id'])

# Function to manage Stop Loss and Take Profit based on risk/reward
def manage_risk(entry_price, direction):
    risk_reward_ratio = 2  # Risk/Reward ratio of 1:2 or 1:3

    # Calculate Stop Loss and Take Profit based on market structure
    if direction == "Bullish":
        stop_loss = entry_price * 0.98  # 2% stop loss for bullish
        take_profit = entry_price * (1 + 0.02 * risk_reward_ratio)  # TP 2% profit for bullish
    else:
        stop_loss = entry_price * 1.02  # 2% stop loss for bearish
        take_profit = entry_price * (1 - 0.02 * risk_reward_ratio)  # TP 2% profit for bearish

    return stop_loss, take_profit

# Function to check for retracements and entry points
def check_for_entry():
    hh_ll_1d, hh_ll_1h = check_market_structure()

    # Determine market trend and potential entry
    if hh_ll_1d == "Bullish" and hh_ll_1h == "Bullish":
        # Look for entry in the M15 for retracement
        entry_price = get_current_price(symbol)
        stop_loss, take_profit = manage_risk(entry_price, "Bullish")
        execute_trade(entry_price, stop_loss, take_profit)

    elif hh_ll_1d == "Bearish" and hh_ll_1h == "Bearish":
        # Look for entry in the M15 for retracement
        entry_price = get_current_price(symbol)
        stop_loss, take_profit = manage_risk(entry_price, "Bearish")
        execute_trade(entry_price, stop_loss, take_profit)

# Function to run the bot every minute
def run_bot():
    schedule.every(1).minute.do(check_for_entry)

    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/ping', methods=['GET'])
def ping():
    return "Bot is running"

if __name__ == '__main__':
    # Run the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Run Flask app for Telegram Webhook
    app.run(host='0.0.0.0', port=5000)
