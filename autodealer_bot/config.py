"""Конфигурация основного бота из переменных окружения."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_dotenv_file(filepath: str = str(PROJECT_ROOT / ".env")):
    """Простой локальный парсер .env файла"""
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val

# Пробуем подгрузить .env при наличии
load_dotenv_file()

TOKEN = os.getenv("BOT_TOKEN")

_chat_id = os.getenv("YOUR_CHAT_ID")
if _chat_id:
    try:
        YOUR_CHAT_ID = int(_chat_id)
    except ValueError:
        YOUR_CHAT_ID = None
else:
    YOUR_CHAT_ID = None

# Выбор пути БД: если задана переменная DB_NAME — используем её,
# иначе храним локальные данные в отдельной папке data/.
DB_NAME = os.getenv("DB_NAME", str(PROJECT_ROOT / "data" / "instagram_users.db"))
