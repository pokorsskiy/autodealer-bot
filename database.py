"""
Модуль для работы с базой данных SQLite.
"""

import sqlite3
import os
from datetime import datetime
from config import DB_NAME
from logger import log_db, log_error

def init_db():
    """Инициализация базы данных и таблицы instagram_users"""
    try:
        # Автоматически создаем директорию для базы (важно для /data Volume)
        db_dir = os.path.dirname(DB_NAME)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS instagram_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    added_at TEXT
                )
            ''')
            conn.commit()
            log_db("INIT", f"База данных готова по пути: {DB_NAME}")
    except Exception as e:
        log_error("init_db", e)
        raise e

def is_new_instagram_user(user_id: int) -> bool:
    """Проверка, новый ли пользователь из Instagram"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM instagram_users WHERE user_id = ?", (user_id,))
            exists = cur.fetchone() is not None
            return not exists
    except Exception as e:
        log_error("is_new_instagram_user", e)
        return False

def save_instagram_user(user_id: int, username: str | None, first_name: str | None):
    """Сохранение нового пользователя в базу данных"""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO instagram_users (user_id, username, first_name, added_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, now))
            conn.commit()
            log_db("SAVE_USER", f"Сохранен пользователь ID: {user_id} (@{username})")
    except Exception as e:
        log_error("save_instagram_user", e)
