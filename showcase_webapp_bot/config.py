"""Конфигурация Telegram Web App, каталога и закрытой админки."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _local_env() -> dict[str, str]:
    result: dict[str, str] = {}
    path = BASE_DIR / ".env"
    if path.exists():
        with path.open(encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    result[key.strip()] = value.strip().strip("'\"")
    return result


def _value(local_name: str, environment_name: str, default: str = "") -> str:
    return ENV.get(local_name) or os.getenv(environment_name) or default


ENV = _local_env()
TOKEN = _value("BOT_TOKEN", "SHOWCASE_WEBAPP_BOT_TOKEN")
_admin_id = _value("YOUR_CHAT_ID", "SHOWCASE_WEBAPP_ADMIN_CHAT_ID")
try:
    YOUR_CHAT_ID = int(_admin_id) if _admin_id else None
except ValueError:
    YOUR_CHAT_ID = None

WEB_APP_URL = _value("WEB_APP_URL", "SHOWCASE_WEB_APP_URL")
DB_NAME = _value(
    "DB_NAME", "SHOWCASE_WEBAPP_DB_NAME", "showcase_webapp_leads.db"
)
if not os.path.isabs(DB_NAME):
    DB_NAME = str(BASE_DIR / DB_NAME)

ADMIN_USERNAME = _value("ADMIN_USERNAME", "SHOWCASE_WEBAPP_ADMIN_USERNAME")
ADMIN_PASSWORD = _value("ADMIN_PASSWORD", "SHOWCASE_WEBAPP_ADMIN_PASSWORD")
SECRET_KEY = _value("SECRET_KEY", "SHOWCASE_WEBAPP_SECRET_KEY")
WEB_HOST = _value("WEB_HOST", "SHOWCASE_WEBAPP_HOST", "127.0.0.1")
try:
    WEB_PORT = int(_value("WEB_PORT", "SHOWCASE_WEBAPP_PORT", "8000"))
except ValueError:
    WEB_PORT = 8000

UPLOAD_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_MB = 8
SESSION_COOKIE_SECURE = _value(
    "SESSION_COOKIE_SECURE", "SHOWCASE_WEBAPP_COOKIE_SECURE", "1"
).lower() not in {"0", "false", "no"}
