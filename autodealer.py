import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import sqlite3
import os

# ←←← ВСТАВЬ СВОЙ ТОКЕН СЮДА ↓↓↓
TOKEN = '8474300409:AAHxtqti-SYLiJNwUoRPJzfYxBujQquaj3I'

bot = telebot.TeleBot(TOKEN)

# Твой ID для уведомлений и /stats
MY_ID = 8797871373

# Путь к базе на Railway Volume
DB_FILE = '/app/instagram_users.db'


def init_db():
    """Полная очистка + создание новой упрощённой таблицы"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Удаляем старую таблицу (если есть)
    c.execute("DROP TABLE IF EXISTS instagram_users")

    # Создаём новую с 3 столбцами
    c.execute('''CREATE TABLE instagram_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT
                )''')
    conn.commit()
    conn.close()
    print("🗑️ База данных полностью очищена и пересоздана")


def register_instagram_user(user):
    """Возвращает True — если пользователь новый"""
    user_id = user.id
    username = f"@{user.username}" if user.username else None
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT user_id FROM instagram_users WHERE user_id = ?", (user_id,))
    exists = c.fetchone() is not None

    if not exists:
        c.execute("""INSERT INTO instagram_users 
                     (user_id, username, full_name)
                     VALUES (?, ?, ?)""",
                  (user_id, username, full_name))
        conn.commit()
        conn.close()
        return True
    else:
        c.execute("""UPDATE instagram_users 
                     SET username = ?, full_name = ? 
                     WHERE user_id = ?""", (username, full_name, user_id))
        conn.commit()
        conn.close()
        return False


def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM instagram_users")
    total_users = c.fetchone()[0]

    c.execute("""SELECT username, full_name 
                 FROM instagram_users 
                 ORDER BY user_id DESC LIMIT 10""")
    recent = c.fetchall()

    conn.close()

    text = f"""📊 <b>Статистика Instagram-клиентов</b>

Всего уникальных клиентов: <b>{total_users}</b>

🔄 Последние 10 клиентов:
"""
    if recent:
        for i, (username, name) in enumerate(recent, 1):
            user = username or "без username"
            text += f"{i}. {user} — {name or '—'}\n"
    else:
        text += "Пока нет клиентов\n"

    return text


def main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("📢 Группа в Telegram", url="https://t.me/dealer_auto")
    btn2 = InlineKeyboardButton("✍️ Группа МАХ",
                                url="https://max.ru/join/zA6Fz1aond_GxUYLWJDjFGWLRz2H5l0PoES6koN6WnI")
    btn3 = InlineKeyboardButton("📸 Наш Instagram", url="https://www.instagram.com/autodealer138")
    markup.add(btn1, btn2, btn3)
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    text = message.text
    is_from_instagram = len(text) > 7 and text[7:] == "INSTA"

    if is_from_instagram:
        welcome_text = "👋 Привет! Ты пришёл из Instagram.\n\nВот вся информация по авто из Китая, Японии и Кореи:"

        if register_instagram_user(message.from_user):
            try:
                user = message.from_user
                username = f"@{user.username}" if user.username else "нет username"
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

                notification = f"""🔔 НОВЫЙ клиент из Instagram ✅

Юзер: {username}
Имя: {full_name}
Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Ссылка: https://t.me/{user.username if user.username else 'нет'}"""

                bot.send_message(MY_ID, notification)
            except:
                pass
    else:
        welcome_text = "👋 Привет!\n\nВот вся информация по авто из Китая, Японии и Кореи:"

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=main_menu()
    )


@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != MY_ID:
        bot.send_message(message.chat.id, "⛔ У тебя нет доступа к статистике.")
        return
    try:
        stat_text = get_stats()
        bot.send_message(message.chat.id, stat_text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


# Инициализация (очистка + создание)
init_db()
print("✅ Бот запущен | База очищена (только 3 столбца)")
print(f"📊 База данных: {DB_FILE}")
bot.infinity_polling()