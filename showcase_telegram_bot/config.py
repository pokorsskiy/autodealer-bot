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


def _get_value(name: str, default: str = "") -> str:
    return LOCAL_ENV.get(name) or os.getenv(f"SHOWCASE_TELEGRAM_{name}") or default


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


def _telegram_url(name: str) -> str:
    value = _get_value(name).strip()
    if value.startswith("@"):
        return f"https://t.me/{value[1:]}"
    if value.startswith(("t.me/", "telegram.me/")):
        return f"https://{value}"
    if value.startswith("https://"):
        return value
    return ""


MANAGER_URL = _telegram_url("MANAGER_URL")
REVIEWS_URL = _telegram_url("REVIEWS_URL")
COMMUNITY_URL = _telegram_url("COMMUNITY_URL")
TELEGRAM_CHANNEL_URL = _telegram_url("TELEGRAM_CHANNEL_URL")
VK_URL = _get_value("VK_URL") if _get_value("VK_URL").startswith("https://") else ""
YOUTUBE_URL = _get_value("YOUTUBE_URL") if _get_value("YOUTUBE_URL").startswith("https://") else ""

EUR_RUB_RATE = _get_positive_float("EUR_RUB_RATE", 100.0)
DELIVERY_COST_RUB = _get_non_negative_int("DELIVERY_COST_RUB", 350_000)
OTHER_COSTS_RUB = _get_non_negative_int("OTHER_COSTS_RUB", 100_000)
