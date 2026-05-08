import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

TOKEN = '8474300409:AAHxtqti-SYLiJNwUoRPJzfYxBujQquaj3I'
bot = telebot.TeleBot(TOKEN)
MY_ID = 8797871373


@bot.message_handler(commands=['start'])
def start(message):
    is_instagram = "INSTA" in (message.text or "")
    text = "👋 Привет! Ты пришёл из Instagram.\n\nВот вся информация по авто из Китая, Японии и Кореи:" if is_instagram else "👋 Привет!\n\nВот вся информация по авто из Китая, Японии и Кореи:"

    if is_instagram:
        user = message.from_user
        bot.send_message(MY_ID, f"🔔 Новый клиент!\nЮзер: @{user.username or 'нет'}")

    bot.send_message(message.chat.id, text, reply_markup=main_menu())


def main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📢 Группа в Telegram", url="https://t.me/dealer_auto"))
    markup.add(
        InlineKeyboardButton("✍️ Группа МАХ", url="https://max.ru/join/zA6Fz1aond_GxUYLWJDjFGWLRz2H5l0PoES6koN6WnI"))
    markup.add(InlineKeyboardButton("📸 Наш Instagram", url="https://www.instagram.com/autodealer138"))
    return markup


print("✅ Бот запущен!")
bot.infinity_polling()