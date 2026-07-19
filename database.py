"""
Модуль для работы с базой данных SQLite.
"""

import sqlite3
import os
from datetime import datetime
import config
from logger import log_db, log_error

def get_db_path() -> str:
    """Получение гарантированно доступного пути к БД"""
    return config.DB_NAME

def init_db():
    """Инициализация базы данных и таблицы instagram_users с фолбэком по правам доступа"""
    db_path = get_db_path()
    try:
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        with sqlite3.connect(db_path) as conn:
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
            log_db("INIT", f"База данных готова по пути: {db_path}")
    except (PermissionError, sqlite3.OperationalError) as e:
        # Если нет прав записи в переданный путь (например /data/), переключаемся на локальный файл
        log_error("init_db_permission_error", f"{e}. Переключаемся на локальную instagram_users.db")
        config.DB_NAME = "instagram_users.db"
        with sqlite3.connect(config.DB_NAME) as conn:
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
            log_db("INIT_FALLBACK", "База данных создана в локальной папке проекта: instagram_users.db")
    except Exception as e:
        log_error("init_db", e)
        raise e

def is_new_instagram_user(user_id: int) -> bool:
    """Проверка, новый ли пользователь из Instagram"""
    db_path = get_db_path()
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM instagram_users WHERE user_id = ?", (user_id,))
            exists = cur.fetchone() is not None
            return not exists
    except Exception as e:
        log_error("is_new_instagram_user", e)
        return False

def save_instagram_user(user_id: int, username: str | None, first_name: str | None):
    """Сохранение нового пользователя в базу данных"""
    db_path = get_db_path()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT OR REPLACE INTO instagram_users (user_id, username, first_name, added_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, now))
            conn.commit()
            log_db("SAVE_USER", f"Сохранен пользователь ID: {user_id} (@{username})")
    except Exception as e:
        log_error("save_instagram_user", e)
