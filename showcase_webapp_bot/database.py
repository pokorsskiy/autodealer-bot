"""Хранилище заявок из Telegram Web App."""

import sqlite3
from datetime import datetime

from config import DB_NAME


def init_db() -> None:
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS webapp_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                car_interest TEXT NOT NULL,
                purchase_method TEXT NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def save_lead(user_id: int, username: str | None, lead: dict[str, str]) -> None:
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            """
            INSERT INTO webapp_leads
                (user_id, username, name, phone, car_interest, purchase_method, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                lead["name"],
                lead["phone"],
                lead["car_interest"],
                lead["purchase_method"],
                lead["comment"],
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
