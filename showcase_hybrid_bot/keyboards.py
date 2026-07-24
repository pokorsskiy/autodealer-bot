"""Telegram-часть интерфейса гибридного бота."""

from telebot import types


def main_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💬 Как это работает", callback_data="about"),
        types.InlineKeyboardButton("📞 Быстрая заявка", callback_data="quick_lead"),
        types.InlineKeyboardButton("💳 Способы покупки", callback_data="payment_info"),
    )
    return markup


def webapp_keyboard(web_app_url: str) -> types.ReplyKeyboardMarkup | None:
    if not web_app_url.startswith("https://"):
        return None
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚗 Открыть каталог и подбор", web_app=types.WebAppInfo(web_app_url)))
    return markup


def contact_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    return markup
