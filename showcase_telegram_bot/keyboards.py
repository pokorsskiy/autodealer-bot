"""Inline-клавиатуры демонстрационного Telegram-бота."""

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


def main_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧮 Калькулятор", callback_data="calculator"),
        _url_or_stub("📞 Связаться", MANAGER_URL, "manager"),
        types.InlineKeyboardButton("⭐ Отзывы", callback_data="reviews"),
        types.InlineKeyboardButton("💬 Общий чат", callback_data="community"),
        types.InlineKeyboardButton("❓ Популярные вопросы", callback_data="faq"),
        types.InlineKeyboardButton("🌐 Другие соцсети", callback_data="socials"),
    )
    return markup


def back_to_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("← Назад в меню", callback_data="menu"))
    return markup


def calculator_cancel() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Отменить расчёт", callback_data="menu"))
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
        _url_or_stub("📞 Уточнить расчёт у менеджера", MANAGER_URL, "manager"),
        types.InlineKeyboardButton("🧮 Новый расчёт", callback_data="calculator"),
        types.InlineKeyboardButton("← Назад в меню", callback_data="menu"),
    )
    return markup


def reviews_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        _url_or_stub("Открыть отзывы", REVIEWS_URL, "reviews"),
        types.InlineKeyboardButton("← Назад в меню", callback_data="menu"),
    )
    return markup


def community_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        _url_or_stub("Перейти в общий чат", COMMUNITY_URL, "community"),
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
