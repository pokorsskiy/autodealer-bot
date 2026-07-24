"""Первый showcase: подбор автомобиля полностью внутри Telegram."""

import html

import telebot
from telebot import types

from config import TOKEN, YOUR_CHAT_ID
from database import init_db, save_lead
from keyboards import catalog_menu, contact_keyboard, main_menu, purchase_menu, remove_reply_keyboard
from logger import logger, safe_handler


if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Укажите его в .env или переменных окружения.")

bot = telebot.TeleBot(TOKEN)
lead_drafts: dict[int, dict[str, str]] = {}


def _send_main_menu(chat_id: int, first_name: str | None = None) -> None:
    greeting = f", {html.escape(first_name)}" if first_name else ""
    bot.send_message(
        chat_id,
        f"👋 <b>Добро пожаловать{greeting}!</b>\n\n"
        "Это демо обычного Telegram-бота: вся навигация и заявка проходят прямо в чате.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


def _send_lead_to_admin(user: types.User, draft: dict[str, str], phone: str) -> None:
    if not YOUR_CHAT_ID:
        logger.warning("Заявка не отправлена: YOUR_CHAT_ID не настроен")
        return
    username = f"@{html.escape(user.username)}" if user.username else "не указан"
    text = (
        "🔥 <b>Новая заявка из Telegram-демо</b>\n\n"
        f"🚗 <b>Автомобиль:</b> {html.escape(draft['car_interest'])}\n"
        f"💳 <b>Покупка:</b> {html.escape(draft['purchase_method'])}\n"
        f"📞 <b>Телефон:</b> <code>{html.escape(phone)}</code>\n\n"
        f"👤 <b>Клиент:</b> {html.escape(user.first_name or 'Без имени')}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>"
    )
    bot.send_message(YOUR_CHAT_ID, text, parse_mode="HTML")


@bot.message_handler(commands=["start", "menu"])
@safe_handler(bot)
def start(message: types.Message) -> None:
    lead_drafts.pop(message.from_user.id, None)
    _send_main_menu(message.chat.id, message.from_user.first_name)


@bot.callback_query_handler(func=lambda call: True)
@safe_handler(bot)
def handle_callback(call: types.CallbackQuery) -> None:
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    if call.data == "menu":
        _send_main_menu(call.message.chat.id, call.from_user.first_name)
    elif call.data == "catalog":
        bot.send_message(call.message.chat.id, "🚘 <b>Автомобили в демо-каталоге</b>\nВыберите модель:", parse_mode="HTML", reply_markup=catalog_menu())
    elif call.data.startswith("car:"):
        car = call.data.removeprefix("car:")
        lead_drafts[user_id] = {"car_interest": car}
        bot.send_message(
            call.message.chat.id,
            f"🚘 <b>{html.escape(car)}</b> выбрана.\n\nКак планируете покупку?",
            parse_mode="HTML",
            reply_markup=purchase_menu(),
        )
    elif call.data == "lead:start":
        lead_drafts[user_id] = {"car_interest": "Нужен подбор автомобиля"}
        bot.send_message(call.message.chat.id, "Какой способ покупки вам удобен?", reply_markup=purchase_menu())
    elif call.data == "payment_info":
        bot.send_message(call.message.chat.id, "💳 Доступны наличные, кредит и трейд-ин. Для точного расчёта оставьте заявку.", reply_markup=main_menu())
    elif call.data.startswith("payment:"):
        draft = lead_drafts.setdefault(user_id, {"car_interest": "Нужен подбор автомобиля"})
        draft["purchase_method"] = call.data.removeprefix("payment:")
        bot.send_message(
            call.message.chat.id,
            "📱 Отправьте номер телефона системной кнопкой ниже — менеджер подготовит предложение.",
            reply_markup=contact_keyboard(),
        )


@bot.message_handler(content_types=["contact"])
@safe_handler(bot)
def handle_contact(message: types.Message) -> None:
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "Отправьте, пожалуйста, свой номер телефона.", reply_markup=contact_keyboard())
        return
    _finish_lead(message, message.contact.phone_number)


@bot.message_handler(func=lambda message: True, content_types=["text"])
@safe_handler(bot)
def handle_text(message: types.Message) -> None:
    draft = lead_drafts.get(message.from_user.id)
    if draft and "purchase_method" in draft:
        _finish_lead(message, message.text.strip())
    else:
        _send_main_menu(message.chat.id, message.from_user.first_name)


def _finish_lead(message: types.Message, phone: str) -> None:
    draft = lead_drafts.get(message.from_user.id)
    if not draft or not draft.get("purchase_method"):
        bot.send_message(message.chat.id, "Сначала выберите автомобиль и способ покупки.", reply_markup=main_menu())
        return
    if len(phone) < 5 or len(phone) > 30:
        bot.send_message(message.chat.id, "Проверьте номер телефона и отправьте его ещё раз.", reply_markup=contact_keyboard())
        return

    _send_lead_to_admin(message.from_user, draft, phone)
    save_lead(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        draft["car_interest"],
        draft["purchase_method"],
        phone,
    )
    lead_drafts.pop(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        "✅ <b>Заявка принята!</b> Менеджер свяжется с вами в ближайшее время.",
        parse_mode="HTML",
        reply_markup=remove_reply_keyboard(),
    )
    _send_main_menu(message.chat.id)


if __name__ == "__main__":
    init_db()
    logger.info("Первый showcase-бот запущен")
    bot.infinity_polling(skip_pending=True)
