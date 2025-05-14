import requests

TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
CHAT_ID = '8104629569'

msg = "✅ ทดสอบส่งข้อความ Telegram จากบอท"

url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
data = {'chat_id': CHAT_ID, 'text': msg}

response = requests.post(url, data=data)
print(response.status_code)
print(response.text)
