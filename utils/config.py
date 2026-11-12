import os

class Config:
    UPLOAD_FOLDER = "data"
    HISTORY_FOLDER = "history"

    ALLOWED_EXTENSIONS = {"csv", "xlsx"}

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    ALERT_DAYS = 10

    KEY_COLUMN = "APPL_ID"

    EXCLUDED_COMPARE_COLUMNS = []