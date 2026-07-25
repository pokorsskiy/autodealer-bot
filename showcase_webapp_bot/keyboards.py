"""Inline-клавиатура открытия Web App."""

from telebot import types


def webapp_keyboard(url: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🚗 Открыть Web App",
            web_app=types.WebAppInfo(url=url),
        )
    )
    return markup
