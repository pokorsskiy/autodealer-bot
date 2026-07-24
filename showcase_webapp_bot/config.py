"""Конфигурация второго демонстрационного бота."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _local_env() -> dict[str, str]:
    result: dict[str, str] = {}
    path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    result[key.strip()] = value.strip().strip("'\"")
    return result


ENV = _local_env()
TOKEN = ENV.get("BOT_TOKEN") or os.getenv("SHOWCASE_WEBAPP_BOT_TOKEN")
_admin_id = ENV.get("YOUR_CHAT_ID") or os.getenv("SHOWCASE_WEBAPP_ADMIN_CHAT_ID")
try:
    YOUR_CHAT_ID = int(_admin_id) if _admin_id else None
except ValueError:
    YOUR_CHAT_ID = None

WEB_APP_URL = ENV.get("WEB_APP_URL") or os.getenv("SHOWCASE_WEB_APP_URL") or ""
DB_NAME = ENV.get("DB_NAME") or os.getenv("SHOWCASE_WEBAPP_DB_NAME") or "showcase_webapp_leads.db"
if not os.path.isabs(DB_NAME):
    DB_NAME = os.path.join(BASE_DIR, DB_NAME)
