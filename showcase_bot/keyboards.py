"""Клавиатуры бота-витрины."""

from telebot import types

from .config import SHOWCASES, SUPPORT_URL


def get_main_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🤖 Примеры ботов", callback_data="catalog"),
        types.InlineKeyboardButton("🛠 Разработка под заказ", callback_data="lead:start"),
        types.InlineKeyboardButton("📞 Поддержка", callback_data="support"),
    )
    return markup


def get_catalog_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in SHOWCASES:
        markup.add(
            types.InlineKeyboardButton(item["title"], callback_data=f"showcase:{item['key']}")
        )
    markup.add(types.InlineKeyboardButton("← В меню", callback_data="menu"))
    return markup


def get_showcase_keyboard(showcase: dict[str, str]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    if showcase["url"]:
        markup.add(types.InlineKeyboardButton("Открыть бота", url=showcase["url"]))
    markup.add(
        types.InlineKeyboardButton("← К примерам", callback_data="catalog"),
        types.InlineKeyboardButton("В меню", callback_data="menu"),
    )
    return markup


def get_support_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    if SUPPORT_URL:
        markup.add(types.InlineKeyboardButton("Написать в поддержку", url=SUPPORT_URL))
    markup.add(types.InlineKeyboardButton("← В меню", callback_data="menu"))
    return markup
