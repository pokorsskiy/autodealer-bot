import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import sqlite3

# ←←← ВСТАВЬ СВОЙ ТОКЕН СЮДА ↓↓↓
TOKEN = '8474300409:AAHxtqti-SYLiJNwUoRPJzfYxBujQquaj3I'

bot = telebot.TeleBot(TOKEN)

# Твой ID для уведомлений
MY_ID = 8797871373

# Путь к базе на Railway Volume
DB_FILE = '/app/instagram_users.db'


def init_db():
    """Создаём таблицу, если её ещё нет"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS instagram_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    visit_count INTEGER DEFAULT 1
                )''')
    conn.commit()
    conn.close()


def register_instagram_user(user):
    """Возвращает True — если новый (уведомление нужно)"""
    user_id = user.id
    username = f"@{user.username}" if user.username else None
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT visit_count FROM instagram_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    if result is None:
        # Новый пользователь
        c.execute("""INSERT INTO instagram_users 
                     (user_id, username, full_name, first_seen, last_seen, visit_count)
                     VALUES (?, ?, ?, ?, ?, 1)""",
                  (user_id, username, full_name, now, now))
        conn.commit()
        conn.close()
        return True
    else:
        # Повторный
        new_count = result[0] + 1
        c.execute("""UPDATE instagram_users 
                     SET last_seen = ?, visit_count = ? 
                     WHERE user_id = ?""", (now, new_count, user_id))
        conn.commit()
        conn.close()
        return False


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
Время первого визита: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Повторных заходов: 1 (первый)
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


# Инициализация базы
init_db()
print("✅ Бот запущен на Railway с Persistent Volume")
print(f"📊 База данных: {DB_FILE}")
bot.infinity_polling()