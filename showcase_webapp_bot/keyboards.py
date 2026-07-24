"""Клавиатура открытия Web App."""

from telebot import types


def webapp_keyboard(url: str) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚗 Открыть каталог", web_app=types.WebAppInfo(url=url)))
    return markup
