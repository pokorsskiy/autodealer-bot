import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import sqlite3
import os
import traceback

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


def register_instagram_user(user):
    try:
        user_id = user.id
        username = f"@{user.username}" if user.username else None
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id FROM instagram_users WHERE user_id = ?", (user_id,))

        if c.fetchone() is None:
            c.execute("INSERT INTO instagram_users (user_id, username, full_name) VALUES (?, ?, ?)",
                      (user_id, username, full_name))
            conn.commit()
            print(f"✅ Новый клиент сохранён: {user_id}")
            conn.close()
            return True
        conn.close()
        return False
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        return False


def main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📢 Группа в Telegram", url="https://t.me/dealer_auto"))
    markup.add(
        InlineKeyboardButton("✍️ Группа МАХ", url="https://max.ru/join/zA6Fz1aond_GxUYLWJDjFGWLRz2H5l0PoES6koN6WnI"))
    markup.add(InlineKeyboardButton("📸 Наш Instagram", url="https://www.instagram.com/autodealer138"))
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    is_from_instagram = message.text and "INSTA" in message.text

    if is_from_instagram:
        welcome_text = "👋 Привет! Ты пришёл из Instagram.\n\nВот вся информация по авто из Китая, Японии и Кореи:"
        if register_instagram_user(message.from_user):
            user = message.from_user
            notification = f"""🔔 НОВЫЙ клиент из Instagram ✅
Юзер: @{user.username or 'нет'}
Имя: {user.first_name or ''} {user.last_name or ''}
Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
            bot.send_message(MY_ID, notification)
    else:
        welcome_text = "👋 Привет!\n\nВот вся информация по авто из Китая, Японии и Кореи:"

    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())


@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != MY_ID:
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM instagram_users")
        total = c.fetchone()[0]
        conn.close()
        bot.send_message(message.chat.id, f"📊 Всего уникальных клиентов: {total}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка stats: {e}")


@bot.message_handler(commands=['db'])
def send_db_file(message):
    if message.from_user.id != MY_ID:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён")
        return

    try:
        print(f"📤 Команда /db вызвана. Файл существует: {os.path.exists(DB_FILE)}")

        if os.path.exists(DB_FILE):
            file_size = os.path.getsize(DB_FILE)
            print(f"📤 Отправляю файл размером {file_size} байт")

            with open(DB_FILE, 'rb') as db_file:
                bot.send_document(
                    message.chat.id,
                    db_file,
                    caption=f"📁 instagram_users.db\nРазмер: {file_size} байт\nОткрывай в DB Browser for SQLite",
                    filename="instagram_users.db"
                )
            bot.send_message(message.chat.id, "✅ Файл базы отправлен!")
        else:
            bot.send_message(message.chat.id, "❌ Файл базы ещё не создан")
    except Exception as e:
        error_text = f"❌ Ошибка при отправке /db:\n{str(e)}\n{traceback.format_exc()}"
        print(error_text)
        bot.send_message(message.chat.id, error_text)


init_db()
print("✅ Бот запущен успешно | /db улучшен")
bot.infinity_polling()