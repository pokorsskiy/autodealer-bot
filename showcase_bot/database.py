"""
Модуль работы с базой данных SQLite для Бота-Продавца (Showcase Bot).
"""

import sqlite3
import os
from typing import Optional, Dict, Any
from config import DB_NAME


def init_db():
    """Инициализация БД лидов потенциальных покупателей бота"""
    db_dir = os.path.dirname(DB_NAME)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                interest TEXT DEFAULT 'Общий интерес',
                source TEXT DEFAULT 'DIRECT',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    print(f"[INFO] База данных лидов инициализирована: {DB_NAME}")


def save_or_update_lead(user_id: int, username: Optional[str], full_name: Optional[str], source: str = "DIRECT"):
    """Сохранение базовой информации о лиде при старте"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO leads (user_id, username, full_name, source)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
        ''', (user_id, username, full_name, source))
        conn.commit()


def update_lead_contact(user_id: int, phone: str, interest: Optional[str] = None):
    """Обновление контактного телефона и тарифного интереса лида"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        if interest:
            cursor.execute('''
                UPDATE leads
                SET phone = ?, interest = ?
                WHERE user_id = ?
            ''', (phone, interest, user_id))
        else:
            cursor.execute('''
                UPDATE leads
                SET phone = ?
                WHERE user_id = ?
            ''', (phone, user_id))
        conn.commit()


def get_lead(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение информации о лиде по user_id"""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leads WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
