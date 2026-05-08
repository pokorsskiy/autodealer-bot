import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import sqlite3
from datetime import datetime

TOKEN = '8474300409:AAHxtqti-SYLiJNwUoRPJzfYxBujQquaj3I'
bot = telebot.TeleBot(TOKEN)
MY_ID = 8797871373

DB_FILE = '/app/instagram_users.db' if os.path.exists('/app') else 'instagram_users.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS instagram_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT
                )''')
    conn.commit()
    conn.close()
    print(f"✅ База готова → {DB_FILE}")

def main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📢 Группа в Telegram", url="https://t.me/dealer_auto"))
    markup.add(InlineKeyboardButton("✍️ Группа МАХ", url="https://max.ru/join/zA6Fz1aond_GxUYLWJDjFGWLRz2H5l0PoES6koN6WnI"))
    markup.add(InlineKeyboardButton("📸 Наш Instagram", url="https://www.instagram.com/autodealer138"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    is_instagram = message.text and "INSTA" in message.text
    text = "👋 Привет! Ты пришёл из Instagram.\n\nВот вся информация по авто из Китая, Японии и Кореи:" if is_instagram else "👋 Привет!\n\nВот вся информация по авто из Китая, Японии и Кореи:"

    if is_instagram:
        user = message.from_user
        bot.send_message(MY_ID, f"🔔 Новый клиент из Instagram!\nЮзер: @{user.username or 'нет'}\nИмя: {user.first_name or ''}")

    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != MY_ID: return
    bot.send_message(message.chat.id, "✅ Бот работает. Клиенты сохраняются.")

init_db()
print("✅ Бот успешно запущен на Railway!")
bot.infinity_polling()