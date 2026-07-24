"""Работа с заявками первого демонстрационного бота."""

import sqlite3
from datetime import datetime

from config import DB_NAME


def init_db() -> None:
    """Создаёт отдельную БД демо-бота, не изменяя другие базы проекта."""
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                car_interest TEXT,
                purchase_method TEXT,
                phone TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_lead(
    user_id: int,
    username: str | None,
    full_name: str | None,
    car_interest: str,
    purchase_method: str,
    phone: str,
) -> None:
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            """
            INSERT INTO leads (user_id, username, full_name, car_interest, purchase_method, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, full_name, car_interest, purchase_method, phone, datetime.now().isoformat(timespec="seconds")),
        )
