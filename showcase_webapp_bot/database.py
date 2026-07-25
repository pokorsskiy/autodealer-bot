"""Хранилище заявок из Telegram Web App с безопасной миграцией схемы."""

import os
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime

from config import DB_NAME


EXTRA_COLUMNS = {
    "lead_type": "TEXT NOT NULL DEFAULT 'car'",
    "contact_username": "TEXT",
    "car_id": "TEXT",
}


def _table_columns(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("PRAGMA table_info(webapp_leads)").fetchall()
    return {str(row[1]) for row in rows}


def _migrate_db(connection: sqlite3.Connection) -> None:
    missing = {
        name: definition
        for name, definition in EXTRA_COLUMNS.items()
        if name not in _table_columns(connection)
    }
    if not missing:
        return

    if os.path.exists(DB_NAME):
        shutil.copyfile(DB_NAME, f"{DB_NAME}.bak")

    for name, definition in missing.items():
        connection.execute(f"ALTER TABLE webapp_leads ADD COLUMN {name} {definition}")
    connection.commit()


def init_db() -> None:
    with closing(sqlite3.connect(DB_NAME)) as connection:
        with connection:
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
                    created_at TEXT NOT NULL,
                    lead_type TEXT NOT NULL DEFAULT 'car',
                    contact_username TEXT,
                    car_id TEXT
                )
                """
            )
            _migrate_db(connection)


def save_lead(user_id: int, telegram_username: str | None, lead: dict[str, str]) -> None:
    with closing(sqlite3.connect(DB_NAME)) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO webapp_leads (
                    user_id,
                    username,
                    name,
                    phone,
                    car_interest,
                    purchase_method,
                    comment,
                    created_at,
                    lead_type,
                    contact_username,
                    car_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    telegram_username,
                    lead["name"],
                    lead["phone"],
                    lead["car_interest"],
                    lead["purchase_method"],
                    lead["comment"],
                    datetime.now().isoformat(timespec="seconds"),
                    lead["lead_type"],
                    lead["username"],
                    lead["car_id"],
                ),
            )
