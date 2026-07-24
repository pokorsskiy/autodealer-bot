"""Хранилище заявок, собранных в Telegram и в Web App."""

import sqlite3
from datetime import datetime

from config import DB_NAME


def init_db() -> None:
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hybrid_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                lead_type TEXT NOT NULL,
                car_interest TEXT,
                phone TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def save_lead(user_id: int, username: str | None, lead_type: str, car_interest: str, phone: str) -> None:
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            "INSERT INTO hybrid_leads (user_id, username, lead_type, car_interest, phone, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, lead_type, car_interest, phone, datetime.now().isoformat(timespec="seconds")),
        )
