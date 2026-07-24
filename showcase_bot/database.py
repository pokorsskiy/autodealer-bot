"""SQLite-хранилище заявок бота-витрины."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def init_db(db_name: str) -> None:
    """Создаёт таблицу заявок, не затрагивая существующие данные."""
    db_path = Path(db_name)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_lead(
    db_name: str,
    user_id: int,
    username: str | None,
    first_name: str | None,
    description: str,
) -> int:
    """Сохраняет заявку и возвращает её номер."""
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(db_name) as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (user_id, username, first_name, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, first_name, description, created_at),
        )
        return cursor.lastrowid
