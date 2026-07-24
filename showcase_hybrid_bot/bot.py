"""Третий showcase: Telegram-диалог + Web App для подбора."""

import html
import json

import telebot
from telebot import types

from config import TOKEN, WEB_APP_URL, YOUR_CHAT_ID
from database import init_db, save_lead
from keyboards import contact_keyboard, main_menu, webapp_keyboard
from logger import logger, safe_handler

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Скопируйте .env.example в .env и укажите токен.")

bot = telebot.TeleBot(TOKEN)
waiting_for_phone: set[int] = set()


def send_menu(chat_id: int, first_name: str | None = None) -> None:
    name = f", {html.escape(first_name)}" if first_name else ""
    bot.send_message(
        chat_id,
        f"👋 <b>Здравствуйте{name}!</b>\n\n"
        "Это гибридное демо: быстрые вопросы решаются в чате, а каталог открывается в Web App.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
    keyboard = webapp_keyboard(WEB_APP_URL)
    if keyboard:
        bot.send_message(chat_id, "🚗 Для каталога и подробного подбора используйте кнопку ниже.", reply_markup=keyboard)


def notify_admin(user: types.User, phone: str) -> None:
    if not YOUR_CHAT_ID:
        return
    bot.send_message(
        YOUR_CHAT_ID,
        "📞 <b>Быстрая заявка из Hybrid-демо</b>\n\n"
        f"👤 {html.escape(user.first_name or 'Без имени')}\n"
        f"📱 <code>{html.escape(phone)}</code>\n"
        f"🆔 <code>{user.id}</code>",
        parse_mode="HTML",
    )


def notify_webapp_lead(user: types.User, lead: dict[str, str]) -> None:
    if not YOUR_CHAT_ID:
        return
    bot.send_message(
        YOUR_CHAT_ID,
        "🚗 <b>Заявка Web App из Hybrid-демо</b>\n\n"
        f"👤 {html.escape(lead['name'])}\n"
        f"📞 <code>{html.escape(lead['phone'])}</code>\n"
        f"🚘 {html.escape(lead['car_interest'])}\n"
        f"💳 {html.escape(lead['purchase_method'])}\n"
        f"🆔 <code>{user.id}</code>",
        parse_mode="HTML",
    )


@bot.message_handler(commands=["start", "menu"])
@safe_handler(bot)
def start(message: types.Message) -> None:
    waiting_for_phone.discard(message.from_user.id)
    send_menu(message.chat.id, message.from_user.first_name)


@bot.callback_query_handler(func=lambda call: True)
@safe_handler(bot)
def callbacks(call: types.CallbackQuery) -> None:
    bot.answer_callback_query(call.id)
    if call.data == "about":
        bot.send_message(call.message.chat.id, "💬 В Telegram можно быстро получить консультацию. Для выбора автомобиля откройте каталог через Web App.")
    elif call.data == "payment_info":
        bot.send_message(call.message.chat.id, "💳 Доступны наличные, кредит и трейд-ин. Точный расчёт менеджер подготовит после заявки.")
    elif call.data == "quick_lead":
        waiting_for_phone.add(call.from_user.id)
        bot.send_message(call.message.chat.id, "📱 Отправьте номер телефона — мы перезвоним.", reply_markup=contact_keyboard())


@bot.message_handler(content_types=["contact"])
@safe_handler(bot)
def contact(message: types.Message) -> None:
    if message.from_user.id not in waiting_for_phone:
        send_menu(message.chat.id, message.from_user.first_name)
        return
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "Отправьте свой номер телефона.", reply_markup=contact_keyboard())
        return
    finish_quick_lead(message, message.contact.phone_number)


@bot.message_handler(content_types=["web_app_data"])
@safe_handler(bot)
def handle_webapp_data(message: types.Message) -> None:
    try:
        payload = json.loads(message.web_app_data.data)
        lead = {field: str(payload.get(field, "")).strip() for field in ("name", "phone", "car_interest", "purchase_method")}
    except (json.JSONDecodeError, AttributeError):
        lead = {}
    if any(not value or len(value) > 100 for value in lead.values()):
        bot.send_message(message.chat.id, "❌ Не удалось прочитать заявку из каталога.")
        return
    save_lead(message.from_user.id, message.from_user.username, "webapp", lead["car_interest"], lead["phone"])
    notify_webapp_lead(message.from_user, lead)
    bot.send_message(message.chat.id, "✅ Заявка из каталога принята. Менеджер свяжется с вами.")


@bot.message_handler(content_types=["text"])
@safe_handler(bot)
def text(message: types.Message) -> None:
    if message.from_user.id in waiting_for_phone:
        finish_quick_lead(message, message.text.strip())
    else:
        send_menu(message.chat.id, message.from_user.first_name)


def finish_quick_lead(message: types.Message, phone: str) -> None:
    if len(phone) < 5 or len(phone) > 30:
        bot.send_message(message.chat.id, "Проверьте номер и отправьте его ещё раз.", reply_markup=contact_keyboard())
        return
    save_lead(message.from_user.id, message.from_user.username, "telegram_quick", "Быстрая консультация", phone)
    notify_admin(message.from_user, phone)
    waiting_for_phone.discard(message.from_user.id)
    bot.send_message(message.chat.id, "✅ Заявка принята. Для самостоятельного подбора откройте каталог в меню.", reply_markup=types.ReplyKeyboardRemove())
    send_menu(message.chat.id)


if __name__ == "__main__":
    init_db()
    logger.info("Hybrid showcase-бот запущен")
    bot.infinity_polling(skip_pending=True)
