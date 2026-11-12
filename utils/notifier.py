import requests
from utils.config import Config


def send_telegram(message):
    if not Config.TELEGRAM_TOKEN or not Config.TELEGRAM_CHAT_ID:
        print("Telegram config not set")
        return None

    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage"

        payload = {
            "chat_id": Config.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, data=payload)
        return response.json()

    except Exception as e:
        print("Telegram Error:", e)
        return None