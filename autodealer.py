import telebot
import sqlite3
import os
from telebot import types
from datetime import datetime

# ===================== НАСТРОЙКИ =====================
TOKEN = os.getenv('BOT_TOKEN')
YOUR_CHAT_ID = int(os.getenv('YOUR_CHAT_ID'))

bot = telebot.TeleBot(TOKEN)
DB_NAME = '/data/instagram_users.db'   # ← теперь база в Volume!

# ===================== БАЗА ДАННЫХ =====================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS instagram_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            added_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def is_new_instagram_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM instagram_users WHERE user_id = ?", (user_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return not exists

def save_instagram_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute('''
        INSERT INTO instagram_users (user_id, username, first_name, added_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, now))
    conn.commit()
    conn.close()

# ===================== УВЕДОМЛЕНИЕ ТЕБЕ =====================
def notify_new_client(message):
    user = message.from_user
    text = f"""
🔔 **НОВЫЙ КЛИЕНТ ИЗ INSTAGRAM!**

👤 Имя: {user.first_name}
🔗 Username: @{user.username if user.username else 'нет'}
🆔 ID: {user.id}
📅 Когда: {datetime.now().strftime('%d.%m.%Y %H:%M')}
🔗 Перешёл по ссылке: ?start=INSTA
    """
    bot.send_message(YOUR_CHAT_ID, text, parse_mode='Markdown')

# ===================== КОМАНДЫ =====================
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    deep_link = message.text.split()[1] if len(message.text.split()) > 1 else ""

    if deep_link == "INSTA":
        if is_new_instagram_user(user.id):
            save_instagram_user(user.id, user.username, user.first_name)
            notify_new_client(message)
            welcome_text = "👋 Привет! Ты пришёл из Instagram\n\n👇 Вот полезные ссылки 👇"
        else:
            welcome_text = "👋 Привет! Ты уже был у нас\n\n👇 Вот полезные ссылки 👇"

        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("📢 Telegram канал", url="https://t.me/dealer_auto")
        btn2 = types.InlineKeyboardButton("🚀 Канал в МАХ", url="https://max.ru/join/zA6Fz1aond_GxUYLWJDjFGWLRz2H5l0PoES6koN6WnI")
        btn3 = types.InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/autodealer138?igsh=cnFwMW5zMWVnZGFw&utm_source=qr")
        btn4 = types.InlineKeyboardButton("🔔 Заказать", url="https://t.me/dealer_auto/714")
        markup.add(btn1, btn2, btn3, btn4)

        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

    else:
        welcome_text ="👋 Привет! Это бот Dealer Auto\n\n👇 Вот полезные ссылки 👇"
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("📢 Telegram канал", url="https://t.me/dealer_auto")
        btn2 = types.InlineKeyboardButton("🚀 Канал в МАХ",
                                          url="https://max.ru/join/zA6Fz1aond_GxUYLWJDjFGWLRz2H5l0PoES6koN6WnI")
        btn3 = types.InlineKeyboardButton("📸 Instagram",
                                          url="https://www.instagram.com/autodealer138?igsh=cnFwMW5zMWVnZGFw&utm_source=qr")
        btn4 = types.InlineKeyboardButton("🔔 Заказать", url="https://t.me/dealer_auto/714")
        markup.add(btn1, btn2, btn3, btn4)

        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['db'])
def send_db(message):
    if message.from_user.id == YOUR_CHAT_ID:
        try:
            with open(DB_NAME, 'rb') as db_file:
                bot.send_document(message.chat.id, db_file, caption="📂 Вот актуальная база instagram_users.db")
        except:
            bot.send_message(message.chat.id, "❌ База ещё не создана.")
    else:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён.")

# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    init_db()
    print("🚀 Бот запущен на Railway... База в /data/instagram_users.db")
    bot.infinity_polling()