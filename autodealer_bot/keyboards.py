"""
Модуль генерации клавиатур и меню для Telegram бота.
"""

from telebot import types

def get_main_keyboard() -> types.InlineKeyboardMarkup:
    """Генерация главной клавиатуры с полезными ссылками Dealer Auto"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 Telegram канал", url="https://t.me/dealer_auto"),
        types.InlineKeyboardButton("🚀 Канал в МАХ", url="https://max.ru/join/zA6Fz1aond_GxUYLWJDjFGWLRz2H5l0PoES6koN6WnI"),
        types.InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/autodealer138?igsh=cnFwMW5zMWVnZGFw&utm_source=qr"),
        types.InlineKeyboardButton("🔔 Заказать", url="https://t.me/dealer_auto/714")
    )
    return markup
