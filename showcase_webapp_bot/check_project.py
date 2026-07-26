"""Быстрая диагностика Web App showcase."""

import ast
import sys
from pathlib import Path

from config import ADMIN_PASSWORD, ADMIN_USERNAME, SECRET_KEY, WEB_APP_URL


BASE_DIR = Path(__file__).resolve().parent
PYTHON_FILES = [
    BASE_DIR / "bot.py",
    BASE_DIR / "config.py",
    BASE_DIR / "database.py",
    BASE_DIR / "keyboards.py",
    BASE_DIR / "logger.py",
    BASE_DIR / "server.py",
]
WEB_FILES = [
    BASE_DIR / "web" / "index.html",
    BASE_DIR / "web" / "style.css",
    BASE_DIR / "web" / "app.js",
    BASE_DIR / "web" / "admin" / "admin.css",
    BASE_DIR / "web" / "admin" / "admin.js",
    BASE_DIR / "templates" / "login.html",
    BASE_DIR / "templates" / "admin.html",
]


def main() -> int:
    missing = [path.name for path in [*PYTHON_FILES, *WEB_FILES] if not path.exists()]
    if missing:
        print(f"❌ Нет файлов: {', '.join(missing)}")
        return 1
    print("🔍 Файлы: OK")

    for path in PYTHON_FILES:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print("🔍 Python-синтаксис: OK")

    html = WEB_FILES[0].read_text(encoding="utf-8")
    javascript = WEB_FILES[2].read_text(encoding="utf-8")
    admin_html = WEB_FILES[6].read_text(encoding="utf-8")
    admin_js = WEB_FILES[4].read_text(encoding="utf-8")
    required_html = (
        'id="catalog"',
        'id="lead-form"',
        'id="car-dialog"',
        'id="favorites-dialog"',
        'data-location-jump="city"',
        'data-view="grid"',
        "telegram-web-app.js",
    )
    required_js = (
        'fetch("/api/cars"',
        "telegram.sendData",
        "sessionStorage",
        "calculateDutyEur",
        "openLead",
        "renderFavorites",
    )
    required_admin = (
        'id="car-form"',
        'id="photo-upload"',
        "/api/admin/cars",
        "X-CSRF-Token",
    )
    if not all(marker in html for marker in required_html):
        print("❌ HTML: отсутствуют обязательные разделы")
        return 1
    if not all(marker in javascript for marker in required_js):
        print("❌ JavaScript: отсутствуют обязательные сценарии")
        return 1
    if "favoritesOnly" in javascript:
        print("❌ JavaScript: избранное не должно менять фильтры каталога")
        return 1
    if not all(marker in f"{admin_html}\n{admin_js}" for marker in required_admin):
        print("❌ Админка: отсутствуют обязательные сценарии")
        return 1
    print("🔍 Web App и админка: OK")

    print(f"🔍 HTTPS URL: {'настроен' if WEB_APP_URL.startswith('https://') else 'нужно настроить'}")
    print(
        "🔍 Владелец: "
        + ("настроен" if ADMIN_USERNAME and len(ADMIN_PASSWORD) >= 12 else "нужно настроить")
    )
    print(
        "🔍 SECRET_KEY: "
        + ("настроен" if len(SECRET_KEY) >= 32 else "нужно настроить")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
