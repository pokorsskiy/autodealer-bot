"""Локальная диагностика первого демонстрационного Telegram-бота."""

import ast
import os
import sqlite3

from config import DB_NAME, TOKEN, YOUR_CHAT_ID
from database import init_db


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def check_syntax() -> bool:
    valid = True
    for file_name in os.listdir(BASE_DIR):
        if not file_name.endswith(".py"):
            continue
        path = os.path.join(BASE_DIR, file_name)
        try:
            with open(path, encoding="utf-8") as source:
                ast.parse(source.read(), filename=path)
        except SyntaxError as error:
            print(f"❌ {file_name}: {error}")
            valid = False
    return valid


if __name__ == "__main__":
    print("🔍 Синтаксис:", "OK" if check_syntax() else "ошибка")
    print("🔍 BOT_TOKEN:", "настроен" if TOKEN else "не задан")
    print("🔍 YOUR_CHAT_ID:", "настроен" if YOUR_CHAT_ID else "не задан")
    init_db()
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute("SELECT 1 FROM leads LIMIT 1")
    print("🔍 SQLite:", "OK")
