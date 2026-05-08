import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# ←←← ВСТАВЬ СВОЙ ТОКЕН СЮДА ↓↓↓
TOKEN = '8474300409:AAHxtqti-SYLiJNwUoRPJzfYxBujQquaj3I'

bot = telebot.TeleBot(TOKEN)

# Твой ID для уведомлений
MY_ID = 8797871373


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

        # Автоматическое уведомление тебе
        try:
            user = message.from_user
            username = f"@{user.username}" if user.username else "нет username"
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

            notification = f"""🔔 Новый клиент из Instagram ✅

Юзер: {username}
Имя: {full_name}
Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Ссылка: https://t.me/{user.username if user.username else 'нет'}"""

            bot.send_message(MY_ID, notification)
        except:
            pass  # если вдруг ошибка — не ломаем бота
    else:
        welcome_text = "👋 Привет!\n\nВот вся информация по авто из Китая, Японии и Кореи:"

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=main_menu()
    )


print("✅ Бот запущен и работает 24/7...")
bot.infinity_polling()