"""Клавиатуры первого демонстрационного бота."""

from telebot import types


def main_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚗 Каталог", callback_data="catalog"),
        types.InlineKeyboardButton("🧮 Подобрать авто", callback_data="lead:start"),
        types.InlineKeyboardButton("💳 Варианты покупки", callback_data="payment_info"),
        types.InlineKeyboardButton("📞 Связаться", callback_data="lead:start"),
    )
    return markup


def catalog_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Toyota Camry", callback_data="car:Toyota Camry"))
    markup.add(types.InlineKeyboardButton("BMW X5", callback_data="car:BMW X5"))
    markup.add(types.InlineKeyboardButton("Geely Monjaro", callback_data="car:Geely Monjaro"))
    markup.add(types.InlineKeyboardButton("← В меню", callback_data="menu"))
    return markup


def purchase_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Наличные", callback_data="payment:Наличные"),
        types.InlineKeyboardButton("Кредит", callback_data="payment:Кредит"),
        types.InlineKeyboardButton("Трейд-ин", callback_data="payment:Трейд-ин"),
        types.InlineKeyboardButton("Нужна консультация", callback_data="payment:Консультация"),
    )
    return markup


def contact_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    return markup


def remove_reply_keyboard() -> types.ReplyKeyboardRemove:
    return types.ReplyKeyboardRemove()
