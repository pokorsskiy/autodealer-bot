"""Showcase-бот с каталогом и заявками внутри Telegram Web App."""

import html
import json
import re
import time

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

from config import TOKEN, WEB_APP_URL, YOUR_CHAT_ID
from database import init_db, save_lead
from keyboards import webapp_keyboard
from logger import logger, safe_handler


REQUIRED_FIELDS = ("name", "phone", "car_interest", "purchase_method", "lead_type")
MAX_LENGTHS = {
    "name": 80,
    "phone": 30,
    "username": 64,
    "car_interest": 80,
    "purchase_method": 40,
    "comment": 500,
    "lead_type": 20,
    "car_id": 80,
}
LEAD_TYPES = {"car", "manager"}

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Укажите его в .env или переменных окружения.")

bot = telebot.TeleBot(TOKEN)


def _parse_lead(raw_data: str) -> dict[str, str] | None:
    try:
        payload = json.loads(raw_data)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None

    lead = {field: str(payload.get(field, "")).strip() for field in MAX_LENGTHS}
    if any(not lead[field] for field in REQUIRED_FIELDS):
        return None
    if any(len(lead[field]) > limit for field, limit in MAX_LENGTHS.items()):
        return None
    if lead["lead_type"] not in LEAD_TYPES:
        return None
    if len(lead["name"]) < 2 or len(re.sub(r"\D", "", lead["phone"])) < 10:
        return None
    if lead["lead_type"] == "manager" and len(lead["comment"]) < 3:
        return None
    return lead


def _notify_admin(user: types.User, lead: dict[str, str]) -> None:
    if not YOUR_CHAT_ID:
        logger.warning("YOUR_CHAT_ID не задан: заявка сохранена без уведомления")
        return

    full_name = html.escape(
        " ".join(
            filter(
                None,
                [getattr(user, "first_name", None), getattr(user, "last_name", None)],
            )
        )
        or lead["name"]
    )
    user_username = getattr(user, "username", None)
    telegram_username = f"@{html.escape(user_username)}" if user_username else "не указан"
    contact_username = html.escape(lead["username"]) or "не указан"
    lead_label = "Заявка на автомобиль" if lead["lead_type"] == "car" else "Помощь с выбором"
    profile = f'<a href="tg://user?id={user.id}">{full_name}</a>'

    bot.send_message(
        YOUR_CHAT_ID,
        f"🔥 <b>{lead_label} из Web App</b>\n\n"
        f"👤 <b>Клиент:</b> {profile}\n"
        f"✍️ <b>Имя в форме:</b> {html.escape(lead['name'])}\n"
        f"📞 <b>Телефон:</b> <code>{html.escape(lead['phone'])}</code>\n"
        f"💬 <b>Username в форме:</b> {contact_username}\n"
        f"🚗 <b>Автомобиль:</b> {html.escape(lead['car_interest'])}\n"
        f"💳 <b>Покупка:</b> {html.escape(lead['purchase_method'])}\n"
        f"📝 <b>Комментарий:</b> {html.escape(lead['comment']) or '—'}\n\n"
        f"🔗 <b>Telegram:</b> {telegram_username}, <code>{user.id}</code>",
        parse_mode="HTML",
    )


def configure_commands() -> None:
    try:
        bot.set_my_commands([types.BotCommand("start", "Открыть Web App")])
        bot.set_chat_menu_button(menu_button=types.MenuButtonCommands(type="commands"))
    except ApiTelegramException:
        logger.exception("Не удалось настроить системное меню Telegram")


@bot.message_handler(commands=["start"])
@safe_handler(bot)
def start(message: types.Message) -> None:
    if not WEB_APP_URL.startswith("https://"):
        bot.send_message(
            message.chat.id,
            "⚠️ Web App ещё не настроен. Публичный HTTPS-адрес будет добавлен позже.",
        )
        return
    bot.send_message(
        message.chat.id,
        "🚗 <b>Dealer Auto Web App</b>\n\n"
        "Каталог, калькулятор и заявка доступны внутри приложения.",
        parse_mode="HTML",
        reply_markup=webapp_keyboard(WEB_APP_URL),
    )


@bot.message_handler(content_types=["web_app_data"])
@safe_handler(bot)
def handle_webapp_data(message: types.Message) -> None:
    lead = _parse_lead(message.web_app_data.data)
    if not lead:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось прочитать заявку. Проверьте поля и попробуйте ещё раз.",
        )
        return

    save_lead(message.from_user.id, message.from_user.username, lead)
    _notify_admin(message.from_user, lead)
    bot.send_message(
        message.chat.id,
        "✅ <b>Заявка принята!</b> Менеджер свяжется с вами в ближайшее время.",
        parse_mode="HTML",
    )


def run_polling() -> None:
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except (ApiTelegramException, OSError):
            logger.exception("Ошибка соединения с Telegram. Повтор через 5 секунд.")
            time.sleep(5)


if __name__ == "__main__":
    init_db()
    configure_commands()
    logger.info("Web App showcase-бот запущен")
    run_polling()
