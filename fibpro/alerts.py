import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        response = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": message
        }, timeout=5)

        if response.status_code != 200:
            raise Exception(response.text)

        return True, "Sent"

    except Exception as e:
        return False, str(e)