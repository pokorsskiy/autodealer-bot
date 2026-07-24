"""Настройки бота-витрины из окружения и локального .env."""

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent


def load_dotenv_file(filepath: Path = PROJECT_DIR / ".env") -> None:
    """Загружает простые пары KEY=VALUE, не перезаписывая окружение."""
    if not filepath.exists():
        return

    for raw_line in filepath.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip().strip("'\""))


load_dotenv_file()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_NAME = os.getenv("DB_NAME", str(PROJECT_DIR / "showcase_leads.db"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "")

try:
    YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID", ""))
except ValueError:
    YOUR_CHAT_ID = None

SHOWCASES = (
    {
        "key": "basic",
        "title": "Telegram-каталог",
        "description": "Каталог, выбор автомобиля и заявка прямо в чате Telegram.",
        "url": os.getenv("TELEGRAM_SHOWCASE_URL", ""),
    },
    {
        "key": "webapp",
        "title": "Каталог в Web App",
        "description": "Витрина автомобилей в интерфейсе Telegram Web App.",
        "url": os.getenv("WEBAPP_SHOWCASE_URL", ""),
    },
    {
        "key": "hybrid",
        "title": "Гибридный бот",
        "description": "Быстрые действия в чате и полный каталог в Web App.",
        "url": os.getenv("HYBRID_SHOWCASE_URL", ""),
    },
    {
        "key": "showcase",
        "title": "Бот-витрина",
        "description": "Презентация решений, сбор заявок и связь с разработчиком.",
        "url": os.getenv("SHOWCASE_BOT_URL", ""),
    },
)
