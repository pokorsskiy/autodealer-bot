"""
Скрипт самодиагностики проекта Бота-Продавца (Showcase Bot).
"""

import os
import sys
import ast
import sqlite3
import urllib.request
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

from config import TOKEN, YOUR_CHAT_ID, DB_NAME, WEB_APP_URL
from database import init_db


def check_python_syntax():
    print("🔍 [1/4] Проверка синтаксиса Python файлов в showcase_bot...")
    has_errors = False
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        ast.parse(f.read(), filename=filepath)
                    print(f"  ✅ {os.path.basename(filepath)} — OK")
                except Exception as e:
                    print(f"  ❌ {os.path.basename(filepath)} — Ошибка синтаксиса: {e}")
                    has_errors = True
    return not has_errors


def check_env_vars():
    print("\n🔍 [2/4] Проверка конфигурации и .env...")
    status = True
    if not TOKEN:
        print("  ⚠️ TOKEN не задан")
        status = False
    else:
        print(f"  ✅ TOKEN — обнаружен (первые 10 символов: {TOKEN[:10]}...)")

    if not YOUR_CHAT_ID:
        print("  ⚠️ YOUR_CHAT_ID не задан")
        status = False
    else:
        print(f"  ✅ YOUR_CHAT_ID — обнаружен ({YOUR_CHAT_ID})")

    if not WEB_APP_URL:
        print("  ⚠️ WEB_APP_URL не задан! Web App не сможет открываться в боте.")
        status = False
    else:
        print(f"  ✅ WEB_APP_URL — обнаружен ({WEB_APP_URL})")

    return status


def check_telegram_api():
    print("\n🔍 [3/4] Проверка соединения с Telegram API...")
    if not TOKEN:
        print("  ⏭ Скип: TOKEN не задан")
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("ok"):
                bot_info = data["result"]
                print(f"  ✅ [Showcase Bot] Успешное подключение! Имя бота: @{bot_info.get('username')}")
                return True
            else:
                print(f"  ❌ Ошибка Telegram API: {data}")
                return False
    except Exception as e:
        print(f"  ❌ Ошибка соединения с Telegram API: {e}")
        return False


def check_database():
    print("\n🔍 [4/4] Проверка Базы Данных SQLite...")
    init_db()

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]
            print(f"  ✅ Подключение к БД {os.path.basename(DB_NAME)} — OK. Таблицы: {tables}")
            return True
    except Exception as e:
        print(f"  ❌ Ошибка подключения к БД: {e}")
        return False


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("==================================================")
    print("🚀 ЗАПУСК ДИАГНОСТИКИ БОТА-ПРОДАВЦА (SHOWCASE BOT)")
    print("==================================================")

    syntax_ok = check_python_syntax()
    env_ok = check_env_vars()
    tg_ok = check_telegram_api()
    db_ok = check_database()

    print("\n==================================================")
    if syntax_ok and env_ok and tg_ok and db_ok:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Бот-Продавец полностью готов к запуску.")
    else:
        print("⚠️ ОБНАРУЖЕНЫ ЗАМЕЧАНИЯ (см. логи выше).")
    print("==================================================")
