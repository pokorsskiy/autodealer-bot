"""
Модуль конфигурации и автоматической загрузки переменных из файла .env
"""

import os

def load_dotenv_file(filepath: str = ".env"):
    """Простой локальный парсер .env файла без сторонних библиотек"""
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

# Загружаем .env при импорте модуля
load_dotenv_file()

TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID_ENV = os.getenv('YOUR_CHAT_ID')

if not TOKEN or TOKEN == "123456789:ABCdefGHIjklMNOpqrsTUVwxyZ":
    print("⚠️ ПРЕДУПРЕЖДЕНИЕ: BOT_TOKEN не задан или содержит шаблонное значение в файле .env!")

YOUR_CHAT_ID = 0
if CHAT_ID_ENV:
    try:
        YOUR_CHAT_ID = int(CHAT_ID_ENV)
    except ValueError:
        print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: YOUR_CHAT_ID должен быть числом, получено: '{CHAT_ID_ENV}'")
else:
    print("⚠️ ПРЕДУПРЕЖДЕНИЕ: YOUR_CHAT_ID не задан в файле .env!")

# Умный выбор пути к БД: если есть Linux Volume /data/ — используем его, иначе локальный файл
if os.getenv('DB_NAME'):
    DB_NAME = os.getenv('DB_NAME')
elif os.path.exists('/data') and os.access('/data', os.W_OK):
    DB_NAME = '/data/instagram_users.db'
else:
    DB_NAME = 'instagram_users.db'
