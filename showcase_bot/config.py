"""
Модуль конфигурации для Telegram Бота-Продавца (Showcase / Демо-бота).
"""

import os

base_dir = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(base_dir, ".env")

local_env = {}
if os.path.exists(env_file_path):
    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            local_env[key.strip()] = val.strip().strip("'\"")

DEFAULT_TOKEN = '8908149919:AAFVQP_mARQfY0NRe1uVSuFUp9wZvjywHtQ'
DEFAULT_CHAT_ID = 8797871373

TOKEN = local_env.get('BOT_TOKEN') or os.getenv('SELLER_BOT_TOKEN') or DEFAULT_TOKEN

chat_id_env = local_env.get('YOUR_CHAT_ID') or os.getenv('YOUR_CHAT_ID')
if chat_id_env:
    try:
        YOUR_CHAT_ID = int(chat_id_env)
    except ValueError:
        YOUR_CHAT_ID = DEFAULT_CHAT_ID
else:
    YOUR_CHAT_ID = DEFAULT_CHAT_ID

default_db_path = os.path.join(base_dir, 'showcase_leads.db')
DB_NAME = local_env.get('DB_NAME') or default_db_path
if not os.path.isabs(DB_NAME):
    DB_NAME = os.path.join(base_dir, DB_NAME)
