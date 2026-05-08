import telebot
import sqlite3
import os
from telebot import types
from datetime import datetime

# ===================== НАСТРОЙКИ =====================
TOKEN = os.getenv('BOT_TOKEN')  # ← будет браться из Railway Variables
YOUR_CHAT_ID = int(os.getenv('YOUR_CHAT_ID'))  # ← твой Telegram ID

bot = telebot.TeleBot(TOKEN)
DB_NAME = 'instagram_users.db'

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
            bot.send_message(message.chat.id, "✅ Привет! Ты пришёл из Instagram. Я запомнил тебя.")
        else:
            bot.send_message(message.chat.id, "👋 Привет! Ты уже был у нас по ссылке из Instagram.")
    else:
        bot.send_message(message.chat.id, "👋 Привет! Это бот Авто из Азии.")

    # Главное меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Подобрать авто", "📦 Рассчитать стоимость")
    markup.add("❓ Задать вопрос", "📞 Консультация")
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

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

# ===================== ОБРАБОТКА КНОПОК =====================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "🔍 Подобрать авто":
        bot.send_message(message.chat.id, "Напиши марку и модель авто из Азии, которое ищешь 👇")
    elif message.text == "📦 Рассчитать стоимость":
        bot.send_message(message.chat.id, "Отправь ссылку на авто с аукциона (Copart, IAAI, Manheim и т.д.)")
    elif message.text == "❓ Задать вопрос":
        bot.send_message(message.chat.id, "Задай свой вопрос — я передам менеджеру")
    elif message.text == "📞 Консультация":
        bot.send_message(message.chat.id, "📲 Менеджер свяжется с тобой в ближайшее время!")
    else:
        bot.send_message(message.chat.id, "✅ Записал. Скоро ответим!")

# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    init_db()
    print("🚀 Бот запущен на Railway...")
    bot.infinity_polling()