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


def normalize_telegram_url(value: str) -> str:
    """Преобразует @username и адрес t.me в допустимый URL для кнопки."""
    url = value.strip()
    if url.startswith("@"):
        return f"https://t.me/{url[1:]}"
    if url.startswith(("t.me/", "telegram.me/")):
        return f"https://{url}"
    if url.startswith(("https://", "http://")):
        return url
    return ""


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_NAME = os.getenv("DB_NAME", str(PROJECT_DIR / "showcase_leads.db"))
SUPPORT_URL = normalize_telegram_url(os.getenv("SUPPORT_URL", ""))
MENU_COVER_FILE_ID = os.getenv("MENU_COVER_FILE_ID", "")

try:
    YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID", ""))
except ValueError:
    YOUR_CHAT_ID = None

SHOWCASES = (
    {
        "key": "basic",
        "title": "Telegram-каталог",
        "description": "Показывает каталог автомобилей, помогает выбрать вариант покупки и принимает заявки прямо в Telegram.",
        "url": normalize_telegram_url(os.getenv("TELEGRAM_SHOWCASE_URL", "")),
    },
    {
        "key": "webapp",
        "title": "Web App-каталог",
        "description": "Полноценная витрина автомобилей внутри Telegram с подробной формой заявки и передачей данных менеджеру.",
        "url": normalize_telegram_url(os.getenv("WEBAPP_SHOWCASE_URL", "")),
    },
    {
        "key": "hybrid",
        "title": "Гибридный бот",
        "description": "Быстрые консультации и заявки работают в чате, а подробный каталог и подбор автомобиля открываются внутри Telegram.",
        "url": normalize_telegram_url(os.getenv("HYBRID_SHOWCASE_URL", "")),
    },
)
