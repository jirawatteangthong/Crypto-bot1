import requests

TOKEN = '7752789264:AAF-0zdgHsSSYe7PS17ePYThOFP3k7AjxBY'
CHAT_ID = '8104629569'
MESSAGE = 'ทดสอบการแจ้งเตือนจากบอท'

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = {
    "chat_id": CHAT_ID,
    "text": MESSAGE
}
response = requests.post(url, data=data)
print(response.status_code, response.text)
