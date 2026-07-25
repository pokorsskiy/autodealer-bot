"""Быстрая диагностика Web App showcase."""

import ast
import sys
from pathlib import Path

from config import WEB_APP_URL


BASE_DIR = Path(__file__).resolve().parent
PYTHON_FILES = [
    BASE_DIR / "bot.py",
    BASE_DIR / "config.py",
    BASE_DIR / "database.py",
    BASE_DIR / "keyboards.py",
    BASE_DIR / "logger.py",
]
WEB_FILES = [
    BASE_DIR / "web" / "index.html",
    BASE_DIR / "web" / "style.css",
    BASE_DIR / "web" / "app.js",
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
    required_html = (
        'id="catalog"',
        'id="calculator"',
        'id="lead-form"',
        'id="car-dialog"',
        "telegram-web-app.js",
    )
    required_js = (
        "telegram.sendData",
        "sessionStorage",
        "filteredCars",
        "calculateDutyEur",
    )
    if not all(marker in html for marker in required_html):
        print("❌ HTML: отсутствуют обязательные разделы")
        return 1
    if not all(marker in javascript for marker in required_js):
        print("❌ JavaScript: отсутствуют обязательные сценарии")
        return 1
    print("🔍 Web App-структура: OK")

    print(f"🔍 HTTPS URL: {'настроен' if WEB_APP_URL.startswith('https://') else 'нужно настроить'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
