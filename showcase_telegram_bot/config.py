"""Конфигурация первого демонстрационного бота."""

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")


def _load_local_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not os.path.exists(ENV_FILE):
        return values

    with open(ENV_FILE, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    return values


LOCAL_ENV = _load_local_env()
TOKEN = LOCAL_ENV.get("BOT_TOKEN") or os.getenv("SHOWCASE_TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

_chat_id = LOCAL_ENV.get("YOUR_CHAT_ID") or os.getenv("SHOWCASE_TELEGRAM_ADMIN_CHAT_ID") or os.getenv("YOUR_CHAT_ID")
try:
    YOUR_CHAT_ID = int(_chat_id) if _chat_id else None
except ValueError:
    YOUR_CHAT_ID = None

DB_NAME = LOCAL_ENV.get("DB_NAME") or os.getenv("SHOWCASE_TELEGRAM_DB_NAME") or "showcase_telegram_leads.db"
if not os.path.isabs(DB_NAME):
    DB_NAME = os.path.join(BASE_DIR, DB_NAME)
