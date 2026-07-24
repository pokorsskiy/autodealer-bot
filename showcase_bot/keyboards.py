"""
Модуль генерации клавиатур для Telegram Бота-Продавца (Showcase Bot).
"""

from telebot import types

def get_webapp_keyboard(web_app_url: str) -> types.ReplyKeyboardMarkup:
    """Генерация клавиатуры с кнопкой запуска Web App"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 Открыть презентацию (Web App)", web_app=types.WebAppInfo(url=web_app_url)))
    return markup

