"""
Скрипт самодиагностики проекта Dealer Auto Bot перед запуском/деплоем.
Проверяет переменные окружения, подключение к Telegram API, синтаксис файлов и SQLite.
"""

import os
import sys
import ast
import sqlite3
import urllib.request
import json

def check_python_syntax():
    print("🔍 [1/4] Проверка синтаксиса Python файлов...")
    has_errors = False
    for root, _, files in os.walk("."):
        if ".venv" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        ast.parse(f.read(), filename=filepath)
                    print(f"  ✅ {filepath} — OK")
                except Exception as e:
                    print(f"  ❌ {filepath} — Ошибка синтаксиса: {e}")
                    has_errors = True
    return not has_errors

def check_env_vars():
    print("\n🔍 [2/4] Проверка переменных окружения...")
    try:
        from config import load_dotenv_file
        load_dotenv_file()
    except Exception:
        pass
        
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("YOUR_CHAT_ID")

    
    status = True
    if not token:
        print("  ⚠️ BOT_TOKEN не найден в окружении (os.getenv)")
        status = False
    else:
        print("  ✅ BOT_TOKEN — обнаружен")
        
    if not chat_id:
        print("  ⚠️ YOUR_CHAT_ID не найден в окружении (os.getenv)")
        status = False
    else:
        print(f"  ✅ YOUR_CHAT_ID — обнаружен ({chat_id})")
        
    return status

def check_telegram_api():
    print("\n🔍 [3/4] Проверка соединения с Telegram API...")
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("  ⏭ Скип: BOT_TOKEN не задан")
        return False
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("ok"):
                bot_info = data["result"]
                print(f"  ✅ Успешное подключение! Имя бота: @{bot_info.get('username')}")
                return True
            else:
                print(f"  ❌ Ошибка Telegram API: {data}")
                return False
    except Exception as e:
        print(f"  ❌ Ошибка соединения с Telegram API: {e}")
        return False

def check_database():
    print("\n🔍 [4/4] Проверка Базы Данных SQLite...")
    db_name = os.getenv("DB_NAME", "instagram_users.db")
    if db_name.startswith("/data/") and not os.path.exists("/data"):
        print(f"  ℹ️ Путь {db_name} указывает на Volume /data (будет доступен на сервере)")
        db_name = "instagram_users.db" # Проверяем локально
        
    try:
        with sqlite3.connect(db_name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]
            print(f"  ✅ Подключение к БД {db_name} — OK. Таблицы: {tables if tables else 'Пока нет таблиц'}")
            return True
    except Exception as e:
        print(f"  ❌ Ошибка подключения к БД: {e}")
        return False

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        
    print("==================================================")
    print("🚀 ЗАПУСК ДИАГНОСТИКИ ПРОЕКТА")
    print("==================================================")
    
    syntax_ok = check_python_syntax()
    env_ok = check_env_vars()
    tg_ok = check_telegram_api()
    db_ok = check_database()
    
    print("\n==================================================")
    if syntax_ok and env_ok and tg_ok and db_ok:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Бот готов к запуску.")
    else:
        print("⚠️ ОБНАРУЖЕНЫ ЗАМЕЧАНИЯ (см. логи выше).")
    print("==================================================")

