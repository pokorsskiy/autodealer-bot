"""Клавиатуры Telegram-части гибридного бота."""

from telebot import types

from config import (
    COMMUNITY_URL,
    MANAGER_URL,
    REVIEWS_URL,
    TELEGRAM_CHANNEL_URL,
    VK_URL,
    YOUTUBE_URL,
)


def _url_or_stub(text: str, url: str, key: str) -> types.InlineKeyboardButton:
    if url:
        return types.InlineKeyboardButton(text, url=url)
    return types.InlineKeyboardButton(text, callback_data=f"stub:{key}")


def _webapp_button(text: str, web_app_url: str) -> types.InlineKeyboardButton:
    if web_app_url.startswith("https://"):
        return types.InlineKeyboardButton(text, web_app=types.WebAppInfo(web_app_url))
    return types.InlineKeyboardButton(text, callback_data="stub:webapp")


def main_menu(web_app_url: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(_webapp_button("🚗 Смотреть автомобили", web_app_url))
    markup.add(
        types.InlineKeyboardButton("🧮 Рассчитать", callback_data="calculator"),
        _url_or_stub("💬 Менеджер", MANAGER_URL, "manager"),
        (
            types.InlineKeyboardButton("⭐ Отзывы", url=REVIEWS_URL)
            if REVIEWS_URL
            else types.InlineKeyboardButton("⭐ Отзывы", callback_data="reviews")
        ),
        (
            types.InlineKeyboardButton("◌ Сообщество", url=COMMUNITY_URL)
            if COMMUNITY_URL
            else types.InlineKeyboardButton("◌ Сообщество", callback_data="community")
        ),
        types.InlineKeyboardButton("❔ Вопросы", callback_data="faq"),
        types.InlineKeyboardButton("◎ Соцсети", callback_data="socials"),
    )
    return markup


def webapp_keyboard(web_app_url: str) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(_webapp_button("🚗 Открыть каталог", web_app_url))
    return markup


def back_to_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("← Назад в меню", callback_data="menu"))
    return markup


def calculator_cancel() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("× Отменить расчёт", callback_data="calc:cancel"))
    return markup


def calculator_mode_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "Знаю стоимость автомобиля",
            callback_data="calc:mode:known",
        ),
        types.InlineKeyboardButton(
            "Укажу ориентир по бюджету",
            callback_data="calc:mode:budget",
        ),
        types.InlineKeyboardButton("× Отменить расчёт", callback_data="calc:cancel"),
    )
    return markup


def age_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("До 3 лет", callback_data="calc:age:under_3"),
        types.InlineKeyboardButton("От 3 до 5 лет", callback_data="calc:age:3_to_5"),
        types.InlineKeyboardButton("Старше 5 лет", callback_data="calc:age:over_5"),
        types.InlineKeyboardButton("← Назад в меню", callback_data="menu"),
    )
    return markup


def result_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        _url_or_stub("🟠 Обсудить с менеджером", MANAGER_URL, "manager"),
        types.InlineKeyboardButton("↻ Новый расчёт", callback_data="calculator"),
        types.InlineKeyboardButton("← Назад в меню", callback_data="menu"),
    )
    return markup


def faq_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Как проходит покупка?", callback_data="faq:purchase"),
        types.InlineKeyboardButton("Сколько занимает доставка?", callback_data="faq:delivery"),
        types.InlineKeyboardButton("Что входит в расчёт?", callback_data="faq:calculation"),
        types.InlineKeyboardButton("Какие нужны документы?", callback_data="faq:documents"),
        types.InlineKeyboardButton("← Назад в меню", callback_data="menu"),
    )
    return markup


def faq_answer_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("← К вопросам", callback_data="faq"),
        types.InlineKeyboardButton("В меню", callback_data="menu"),
    )
    return markup


def socials_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        _url_or_stub("Telegram-канал", TELEGRAM_CHANNEL_URL, "telegram_channel"),
        _url_or_stub("ВКонтакте", VK_URL, "vk"),
        _url_or_stub("YouTube", YOUTUBE_URL, "youtube"),
        types.InlineKeyboardButton("← Назад в меню", callback_data="menu"),
    )
    return markup
