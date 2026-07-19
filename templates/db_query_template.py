"""
Шаблон безопасных запросов к SQLite для мгновенной генерации функций работы с данными.
"""

import sqlite3
import os

DB_NAME = os.getenv("DB_NAME", "instagram_users.db")

def example_db_query(user_id: int):
    """Пример безопасного получения данных"""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT username, first_name FROM instagram_users WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        if result:
            return {"username": result[0], "first_name": result[1]}
        return None
