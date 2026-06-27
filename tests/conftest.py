import os

for _key in [
    "LINE_CHANNEL_ACCESS_TOKEN",
    "LINE_CHANNEL_SECRET",
    "TELEGRAM_BOT_TOKEN",
    "GOOGLE_SHEETS_SPREADSHEET_ID",
    "GOOGLE_SHEETS_CREDENTIALS_JSON",
    "NOTION_TOKEN",
    "NOTION_IDEAS_DB_ID",
]:
    os.environ.setdefault(_key, "test")
