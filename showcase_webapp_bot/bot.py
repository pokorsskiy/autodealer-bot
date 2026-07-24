"""Второй showcase: действия пользователя происходят в Telegram Web App."""

import html
import json

import telebot
from telebot import types

from config import TOKEN, WEB_APP_URL, YOUR_CHAT_ID
from database import init_db, save_lead
from keyboards import webapp_keyboard
from logger import logger, safe_handler

REQUIRED_FIELDS = ("name", "phone", "car_interest", "purchase_method")
MAX_LENGTHS = {"name": 80, "phone": 30, "car_interest": 80, "purchase_method": 40, "comment": 500}

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Укажите его в .env или переменных окружения.")

bot = telebot.TeleBot(TOKEN)


def _parse_lead(raw_data: str) -> dict[str, str] | None:
    try:
        payload = json.loads(raw_data)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    lead = {field: str(payload.get(field, "")).strip() for field in MAX_LENGTHS}
    if any(not lead[field] or len(lead[field]) > MAX_LENGTHS[field] for field in REQUIRED_FIELDS):
        return None
    if len(lead["comment"]) > MAX_LENGTHS["comment"]:
        return None
    return lead


def _notify_admin(user: types.User, lead: dict[str, str]) -> None:
    if not YOUR_CHAT_ID:
        logger.warning("YOUR_CHAT_ID не задан: заявка сохранена без уведомления")
        return
    username = f"@{html.escape(user.username)}" if user.username else "не указан"
    bot.send_message(
        YOUR_CHAT_ID,
        "🔥 <b>Новая заявка из Web App</b>\n\n"
        f"👤 <b>Имя:</b> {html.escape(lead['name'])}\n"
        f"📞 <b>Телефон:</b> <code>{html.escape(lead['phone'])}</code>\n"
        f"🚗 <b>Автомобиль:</b> {html.escape(lead['car_interest'])}\n"
        f"💳 <b>Покупка:</b> {html.escape(lead['purchase_method'])}\n"
        f"📝 <b>Комментарий:</b> {html.escape(lead['comment']) or '—'}\n\n"
        f"🔗 <b>Telegram:</b> {username}, <code>{user.id}</code>",
        parse_mode="HTML",
    )


@bot.message_handler(commands=["start"])
@safe_handler(bot)
def start(message: types.Message) -> None:
    if not WEB_APP_URL.startswith("https://"):
        bot.send_message(message.chat.id, "⚠️ Web App ещё не настроен: укажите публичный HTTPS URL в .env.")
        return
    bot.send_message(
        message.chat.id,
        "🚗 <b>Web App-демо автодилера</b>\n\nНажмите кнопку — каталог и заявка откроются внутри Telegram.",
        parse_mode="HTML",
        reply_markup=webapp_keyboard(WEB_APP_URL),
    )


@bot.message_handler(content_types=["web_app_data"])
@safe_handler(bot)
def handle_webapp_data(message: types.Message) -> None:
    lead = _parse_lead(message.web_app_data.data)
    if not lead:
        bot.send_message(message.chat.id, "❌ Не удалось прочитать заявку. Заполните поля и попробуйте ещё раз.")
        return
    save_lead(message.from_user.id, message.from_user.username, lead)
    _notify_admin(message.from_user, lead)
    bot.send_message(message.chat.id, "✅ <b>Заявка принята!</b> Менеджер свяжется с вами в ближайшее время.", parse_mode="HTML")


if __name__ == "__main__":
    init_db()
    logger.info("Web App showcase-бот запущен")
    bot.infinity_polling(skip_pending=True)
