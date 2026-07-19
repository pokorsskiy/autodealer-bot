"""
Модуль конфигурации и загрузки переменных окружения с гарантированным фолбэком для Railway.
"""

import os

def load_dotenv_file(filepath: str = ".env"):
    """Простой локальный парсер .env файла"""
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

# Пробуем подгрузить .env при наличии
load_dotenv_file()

# Резервные захардкоженные значения для гарантии работы на Railway
DEFAULT_TOKEN = '8474300409:AAHxtqti-SYLiJNwUoRPJzfYxBujQquaj3I'
DEFAULT_CHAT_ID = 8797871373

TOKEN = os.getenv('BOT_TOKEN') or DEFAULT_TOKEN

chat_id_env = os.getenv('YOUR_CHAT_ID')
if chat_id_env:
    try:
        YOUR_CHAT_ID = int(chat_id_env)
    except ValueError:
        YOUR_CHAT_ID = DEFAULT_CHAT_ID
else:
    YOUR_CHAT_ID = DEFAULT_CHAT_ID

# Выбор пути БД: если задана переменная DB_NAME - берем ее, иначе локальный файл в директории бота
DB_NAME = os.getenv('DB_NAME', 'instagram_users.db')
