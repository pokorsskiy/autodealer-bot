"""Конфигурация комбинированного showcase-бота."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return values
    with open(env_path, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
    return values


ENV = _read_env()


def _get_value(name: str, default: str = "") -> str:
    return ENV.get(name) or os.getenv(f"SHOWCASE_HYBRID_{name}") or default


def _get_positive_float(name: str, default: float) -> float:
    try:
        value = float(_get_value(name, str(default)).replace(",", "."))
    except ValueError:
        return default
    return value if value > 0 else default


def _get_non_negative_int(name: str, default: int) -> int:
    try:
        value = int(_get_value(name, str(default)))
    except ValueError:
        return default
    return value if value >= 0 else default


def _https_url(name: str) -> str:
    value = _get_value(name).strip()
    return value if value.startswith("https://") else ""


def _telegram_url(name: str) -> str:
    value = _get_value(name).strip()
    if value.startswith("@"):
        return f"https://t.me/{value[1:]}"
    if value.startswith(("t.me/", "telegram.me/")):
        return f"https://{value}"
    return value if value.startswith("https://") else ""


TOKEN = _get_value("BOT_TOKEN") or os.getenv("BOT_TOKEN")
_admin_id = _get_value("ADMIN_CHAT_ID") or ENV.get("YOUR_CHAT_ID") or os.getenv("YOUR_CHAT_ID")
try:
    YOUR_CHAT_ID = int(_admin_id) if _admin_id else None
except ValueError:
    YOUR_CHAT_ID = None

WEB_APP_URL = _https_url("WEB_APP_URL")
REVIEWS_URL = _telegram_url("REVIEWS_URL")
COMMUNITY_URL = _telegram_url("COMMUNITY_URL")
TELEGRAM_CHANNEL_URL = _telegram_url("TELEGRAM_CHANNEL_URL")
VK_URL = _https_url("VK_URL")
YOUTUBE_URL = _https_url("YOUTUBE_URL")

EUR_RUB_RATE = _get_positive_float("EUR_RUB_RATE", 100.0)
DELIVERY_COST_RUB = _get_non_negative_int("DELIVERY_COST_RUB", 350_000)
OTHER_COSTS_RUB = _get_non_negative_int("OTHER_COSTS_RUB", 100_000)

DB_NAME = _get_value("DB_NAME", "showcase_hybrid_leads.db")
if not os.path.isabs(DB_NAME):
    DB_NAME = os.path.join(BASE_DIR, DB_NAME)
