"""
Модуль генерации клавиатур для Telegram Бота-Продавца (Showcase Bot).
"""

from telebot import types

def get_main_showcase_keyboard() -> types.InlineKeyboardMarkup:
    """Главное меню бота-продавца"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🏎 Тест-драйв (Демо глазами клиента)", callback_data="demo_menu"),
        types.InlineKeyboardButton("✨ Все возможности и фичи", callback_data="features_menu"),
        types.InlineKeyboardButton("💎 Тарифы и стоимость", callback_data="tariffs_menu"),
        types.InlineKeyboardButton("📲 Заказать бота / Бесплатная консультация", callback_data="request_order"),
        types.InlineKeyboardButton("💬 Связаться с продавцом", url="https://t.me/dealer_auto")
    )
    return markup


def get_demo_keyboard() -> types.InlineKeyboardMarkup:
    """Меню интерактивного демо-режима"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🚘 Демо: Посмотреть каталог авто", callback_data="demo_catalog"),
        types.InlineKeyboardButton("🧮 Демо: Расчёт привоза (Корея/Китай)", callback_data="demo_calc"),
        types.InlineKeyboardButton("📩 Демо: Оформить заявку на авто", callback_data="demo_auto_order"),
        types.InlineKeyboardButton("🔙 Вернуться в главное меню", callback_data="main_menu")
    )
    return markup


def get_tariffs_keyboard() -> types.InlineKeyboardMarkup:
    """Меню выбора тарифных планов"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📦 Тариф «Старт» — Бот под ключ", callback_data="select_tariff_start"),
        types.InlineKeyboardButton("🚀 Тариф «Профи» — Бот + Калькулятор", callback_data="select_tariff_pro"),
        types.InlineKeyboardButton("👑 Тариф «VIP» — Выкуп исходного кода", callback_data="select_tariff_vip"),
        types.InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")
    )
    return markup


def get_back_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="main_menu"))
    return markup


def get_contact_reply_keyboard() -> types.ReplyKeyboardMarkup:
    """Reply клавиатура для быстрой отправки контакта"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    markup.add(types.KeyboardButton("❌ Отмена"))
    return markup
