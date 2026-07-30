"""Hybrid showcase: быстрые действия в Telegram и каталог в Web App."""

import html
import json
import re
import time

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

from calculator import (
    AGE_LABELS,
    WEBAPP_DELIVERY_AND_EXPENSES_RUB,
    WEBAPP_EUR_RUB_RATE,
    calculate_total_from_rub,
)
from config import (
    TOKEN,
    WEB_APP_URL,
    YOUR_CHAT_ID,
)
from database import init_db, save_lead
from keyboards import (
    age_menu,
    back_to_menu,
    calculator_cancel,
    calculator_mode_menu,
    faq_answer_menu,
    faq_menu,
    main_menu,
    result_menu,
    socials_menu,
    webapp_keyboard,
)
from logger import logger, safe_handler


REQUIRED_WEBAPP_FIELDS = (
    "name",
    "phone",
    "car_interest",
    "purchase_method",
    "lead_type",
)
WEBAPP_MAX_LENGTHS = {
    "name": 80,
    "phone": 30,
    "username": 64,
    "car_interest": 80,
    "purchase_method": 40,
    "comment": 500,
    "lead_type": 20,
    "car_id": 80,
}
WEBAPP_LEAD_TYPES = {"car", "manager"}

FAQ_ANSWERS = {
    "purchase": (
        "<b>Как проходит покупка?</b>\n\n"
        "Уточняем требования, подбираем автомобиль, согласовываем итоговую смету "
        "и сопровождаем сделку до передачи автомобиля."
    ),
    "delivery": (
        "<b>Сколько занимает доставка?</b>\n\n"
        "Срок зависит от страны, маршрута и загруженности перевозчиков. "
        "Точный прогноз менеджер сообщает после выбора автомобиля."
    ),
    "calculation": (
        "<b>Что входит в расчёт?</b>\n\n"
        "Стоимость автомобиля, ориентировочная таможенная пошлина, доставка "
        "и дополнительные расходы на оформление."
    ),
    "documents": (
        "<b>Какие нужны документы?</b>\n\n"
        "Для предварительного подбора достаточно описания автомобиля и бюджета. "
        "Перечень документов для сделки менеджер сообщит перед оформлением."
    ),
}

STUB_LABELS = {
    "webapp": "Web App",
    "reviews": "Ссылка на отзывы",
    "community": "Ссылка на общий чат",
    "telegram_channel": "Ссылка на Telegram-канал",
    "vk": "Ссылка на ВКонтакте",
    "youtube": "Ссылка на YouTube",
    "manager": "Ссылка на менеджера",
}

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Укажите его в .env или переменных окружения.")

bot = telebot.TeleBot(TOKEN)
calculator_sessions: dict[int, dict[str, object]] = {}
CALCULATOR_TITLE = "🧮 <b>Предварительный расчёт</b>"


def _main_text(first_name: str | None = None) -> str:
    name = f", {html.escape(first_name)}" if first_name else ""
    return (
        f"👋 <b>Добро пожаловать{name}!</b>\n\n"
        "Здесь можно посмотреть автомобили, рассчитать стоимость и связаться с менеджером."
    )


def _format_rub(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _parse_number(value: str) -> float | None:
    normalized = value.replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _parse_rub_price(value: str) -> int | None:
    normalized = (
        value.lower()
        .replace("₽", "")
        .replace("руб.", "")
        .replace("руб", "")
        .replace("\xa0", "")
        .replace(" ", "")
    )
    return int(normalized) if normalized.isdigit() else None


def _parse_engine_liters(value: str) -> float | None:
    normalized = (
        value.lower()
        .replace("литров", "")
        .replace("литра", "")
        .replace("литр", "")
        .replace("л.", "")
        .replace("л", "")
        .strip()
    )
    return _parse_number(normalized)


def _parse_webapp_lead(raw_data: str) -> dict[str, str] | None:
    try:
        payload = json.loads(raw_data)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None

    lead = {
        field: str(payload.get(field, "")).strip()
        for field in WEBAPP_MAX_LENGTHS
    }
    if any(not lead[field] for field in REQUIRED_WEBAPP_FIELDS):
        return None
    if any(
        len(lead[field]) > max_length
        for field, max_length in WEBAPP_MAX_LENGTHS.items()
    ):
        return None
    if lead["lead_type"] not in WEBAPP_LEAD_TYPES:
        return None
    if len(lead["name"]) < 2 or len(re.sub(r"\D", "", lead["phone"])) < 10:
        return None
    if lead["lead_type"] == "manager" and len(lead["comment"]) < 3:
        return None
    return lead


def _profile_text(user: types.User) -> str:
    full_name = html.escape(
        " ".join(
            filter(
                None,
                [getattr(user, "first_name", None), getattr(user, "last_name", None)],
            )
        )
        or "Без имени"
    )
    return f'<a href="tg://user?id={user.id}">{full_name}</a>'


def _notify_webapp_lead(user: types.User, lead: dict[str, str]) -> None:
    if not YOUR_CHAT_ID:
        logger.warning("YOUR_CHAT_ID не задан: Web App-заявка сохранена без уведомления")
        return
    telegram_username = getattr(user, "username", None)
    telegram_username_text = (
        f"@{html.escape(telegram_username)}" if telegram_username else "не указан"
    )
    contact_username = html.escape(lead["username"]) or "не указан"
    lead_label = (
        "Заявка на автомобиль"
        if lead["lead_type"] == "car"
        else "Помощь с выбором"
    )
    bot.send_message(
        YOUR_CHAT_ID,
        f"🔥 <b>{lead_label}</b>\n\n"
        "📍 <b>Источник:</b> Web App\n"
        f"👤 <b>Клиент:</b> {_profile_text(user)}\n"
        f"✍️ <b>Имя в форме:</b> {html.escape(lead['name'])}\n"
        f"📞 <b>Телефон:</b> <code>{html.escape(lead['phone'])}</code>\n"
        f"💬 <b>Username в форме:</b> {contact_username}\n"
        f"🚗 <b>Автомобиль:</b> {html.escape(lead['car_interest'])}\n"
        f"💳 <b>Покупка:</b> {html.escape(lead['purchase_method'])}\n"
        f"📝 <b>Комментарий:</b> {html.escape(lead['comment']) or '—'}\n\n"
        f"🔗 <b>Telegram:</b> {telegram_username_text}, <code>{user.id}</code>",
        parse_mode="HTML",
    )


def _answer_callback(call: types.CallbackQuery, text: str | None = None) -> None:
    try:
        bot.answer_callback_query(call.id, text=text)
    except ApiTelegramException as error:
        if error.error_code == 400:
            logger.info("Устаревший callback %s", call.id)
            return
        raise


def _edit_screen(
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: types.InlineKeyboardMarkup,
) -> None:
    try:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except ApiTelegramException as error:
        description = (error.description or "").lower()
        if error.error_code == 400 and "message is not modified" in description:
            return
        raise


def _send_main_menu(chat_id: int, first_name: str | None = None) -> None:
    _remove_reply_keyboard(chat_id)
    bot.send_message(
        chat_id,
        _main_text(first_name),
        parse_mode="HTML",
        reply_markup=main_menu(WEB_APP_URL),
    )


def _remove_reply_keyboard(chat_id: int) -> None:
    cleanup = bot.send_message(
        chat_id,
        "Клавиатура обновлена.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    try:
        bot.delete_message(chat_id, cleanup.message_id)
    except ApiTelegramException:
        logger.warning("Не удалось удалить техническое сообщение: chat_id=%s", chat_id)


def configure_commands() -> None:
    try:
        bot.set_my_commands(
            [
                types.BotCommand("start", "Запустить бота"),
                types.BotCommand("menu", "Открыть меню"),
                types.BotCommand("site", "Открыть Web App"),
            ]
        )
        bot.set_chat_menu_button(menu_button=types.MenuButtonCommands(type="commands"))
    except ApiTelegramException:
        logger.exception("Не удалось обновить меню команд Telegram")


@bot.message_handler(commands=["start", "menu"])
@safe_handler(bot)
def start(message: types.Message) -> None:
    calculator_sessions.pop(message.from_user.id, None)
    _send_main_menu(message.chat.id, message.from_user.first_name)


@bot.message_handler(commands=["site"])
@safe_handler(bot)
def site(message: types.Message) -> None:
    calculator_sessions.pop(message.from_user.id, None)
    _remove_reply_keyboard(message.chat.id)
    if not WEB_APP_URL.startswith("https://"):
        bot.send_message(
            message.chat.id,
            "⚠️ Web App ещё не настроен. Укажите публичный HTTPS-адрес в WEB_APP_URL.",
        )
        return
    bot.send_message(
        message.chat.id,
        "🚗 <b>Каталог автомобилей</b>\n\n"
        "Здесь есть автомобили в наличии и в порту — с ценами, фотографиями и формой заявки.",
        parse_mode="HTML",
        reply_markup=webapp_keyboard(WEB_APP_URL),
    )


@bot.callback_query_handler(func=lambda call: True)
@safe_handler(bot)
def handle_callback(call: types.CallbackQuery) -> None:
    data = call.data or ""
    user_id = call.from_user.id

    if data.startswith("stub:"):
        key = data.split(":", 1)[1]
        _answer_callback(call, f"{STUB_LABELS.get(key, 'Ссылка')} будет добавлена позже.")
        return

    _answer_callback(call)

    if data == "menu":
        calculator_sessions.pop(user_id, None)
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            _main_text(call.from_user.first_name),
            main_menu(WEB_APP_URL),
        )
        return

    if data == "calculator":
        calculator_message = bot.send_message(
            call.message.chat.id,
            f"{CALCULATOR_TITLE}\n\n"
            "Шаг 1 из 4. Вы знаете стоимость автомобиля за границей?",
            parse_mode="HTML",
            reply_markup=calculator_mode_menu(),
        )
        calculator_sessions[user_id] = {
            "step": "mode",
            "message_id": calculator_message.message_id,
        }
        return

    if data == "calc:cancel":
        calculator_sessions.pop(user_id, None)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except ApiTelegramException as error:
            if error.error_code != 400:
                raise
        return

    if data.startswith("calc:mode:"):
        session = calculator_sessions.get(user_id)
        if not session or session.get("step") != "mode":
            _edit_screen(
                call.message.chat.id,
                call.message.message_id,
                "Расчёт устарел. Начните заново.",
                back_to_menu(),
            )
            return
        price_mode = data.removeprefix("calc:mode:")
        if price_mode not in {"known", "budget"}:
            return
        session["price_mode"] = price_mode
        session["step"] = "price"
        if price_mode == "budget":
            price_prompt = (
                "Шаг 2 из 4. На какую стоимость автомобиля вы ориентируетесь?\n\n"
                "Укажите примерную сумму покупки автомобиля за границей. "
                "Доставку и оформление рассчитаем отдельно.\n\n"
                "Например: <code>3 500 000</code>."
            )
        else:
            price_prompt = (
                "Шаг 2 из 4. Введите стоимость автомобиля за границей.\n\n"
                "Укажите известную стоимость без доставки и оформления.\n\n"
                "Например: <code>3 500 000</code>."
            )
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            f"{CALCULATOR_TITLE}\n\n{price_prompt}",
            calculator_cancel(),
        )
        return

    if data.startswith("calc:age:"):
        session = calculator_sessions.get(user_id)
        if not session or session.get("step") != "age":
            _edit_screen(
                call.message.chat.id,
                call.message.message_id,
                "Расчёт устарел. Начните заново.",
                back_to_menu(),
            )
            return
        age = data.removeprefix("calc:age:")
        if age not in AGE_LABELS:
            return
        session["age"] = age
        session["step"] = "engine"
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            f"{CALCULATOR_TITLE}\n\n"
            "Шаг 4 из 4. Введите объём двигателя в литрах, например: "
            "<code>2.0</code> или <code>1,6 л</code>.",
            calculator_cancel(),
        )
        return

    if data == "reviews":
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            "⭐ <b>Отзывы клиентов</b>\n\nСсылка на отзывы будет добавлена позже.",
            back_to_menu(),
        )
        return

    if data == "community":
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            "💬 <b>Общий чат</b>\n\nСсылка на общий чат будет добавлена позже.",
            back_to_menu(),
        )
        return

    if data == "faq":
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            "❓ <b>Популярные вопросы</b>\n\nВыберите вопрос:",
            faq_menu(),
        )
        return

    if data.startswith("faq:"):
        answer = FAQ_ANSWERS.get(data.split(":", 1)[1])
        if answer:
            _edit_screen(
                call.message.chat.id,
                call.message.message_id,
                answer,
                faq_answer_menu(),
            )
        return

    if data == "socials":
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            "🌐 <b>Другие соцсети</b>\n\nВыберите площадку:",
            socials_menu(),
        )


@bot.message_handler(content_types=["web_app_data"])
@safe_handler(bot)
def handle_webapp_data(message: types.Message) -> None:
    lead = _parse_webapp_lead(message.web_app_data.data)
    if not lead:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось прочитать заявку. Проверьте поля и попробуйте ещё раз.",
        )
        return
    save_lead(
        message.from_user.id,
        message.from_user.username,
        f"webapp_{lead['lead_type']}",
        lead["car_interest"],
        lead["phone"],
    )
    _notify_webapp_lead(message.from_user, lead)
    bot.send_message(
        message.chat.id,
        "✅ <b>Заявка из Web App принята!</b> Менеджер свяжется с вами.",
        parse_mode="HTML",
    )


@bot.message_handler(content_types=["text"])
@safe_handler(bot)
def handle_text(message: types.Message) -> None:
    user_id = message.from_user.id
    session = calculator_sessions.get(user_id)
    if not session:
        _send_main_menu(message.chat.id, message.from_user.first_name)
        return

    if session.get("step") == "price":
        price_rub = _parse_rub_price(message.text or "")
        if (
            price_rub is None
            or not 50_000 <= price_rub <= 50_000_000
            or price_rub % 10_000 != 0
        ):
            bot.send_message(
                message.chat.id,
                "Введите стоимость от 50 000 до 50 000 000 ₽ с шагом 10 000 ₽, "
                "например: <code>2 500 000</code>.",
                parse_mode="HTML",
            )
            return
        session["car_price_rub"] = price_rub
        session["step"] = "age"
        _edit_screen(
            message.chat.id,
            int(session["message_id"]),
            f"{CALCULATOR_TITLE}\n\n"
            "Шаг 3 из 4. Выберите возраст автомобиля:",
            age_menu(),
        )
        return

    if session.get("step") == "engine":
        engine_liters = _parse_engine_liters(message.text or "")
        if (
            engine_liters is None
            or not 0.5 <= engine_liters <= 10
            or abs(engine_liters * 10 - round(engine_liters * 10)) > 1e-9
        ):
            bot.send_message(
                message.chat.id,
                "Введите объём двигателя от 0.5 до 10 л с шагом 0.1 л, например: "
                "<code>2.0</code> или <code>1,6 л</code>.",
                parse_mode="HTML",
            )
            return
        engine_cc = round(engine_liters * 1000)
        age = str(session["age"])
        calculation = calculate_total_from_rub(
            car_price_rub=int(session["car_price_rub"]),
            age=age,
            engine_cc=engine_cc,
            eur_rub_rate=WEBAPP_EUR_RUB_RATE,
            delivery_rub=WEBAPP_DELIVERY_AND_EXPENSES_RUB,
            other_costs_rub=0,
        )
        is_budget = session.get("price_mode") == "budget"
        price_label = "Ориентир на автомобиль" if is_budget else "Автомобиль"
        delivery_and_costs = calculation.delivery_rub + calculation.other_costs_rub
        budget_note = (
            "Расчёт выполнен по указанной ориентировочной стоимости. "
            if is_budget
            else ""
        )
        result_text = (
            "🧮 <b>Ориентировочный расчёт</b>\n\n"
            f"🚘 {price_label}: <b>{_format_rub(calculation.car_price_rub)} ₽</b>\n"
            f"🛃 Таможенная пошлина: <b>{_format_rub(calculation.duty_rub)} ₽</b>\n"
            f"🚚 Доставка и расходы: <b>{_format_rub(delivery_and_costs)} ₽</b>\n\n"
            f"<b>Итого: {_format_rub(calculation.total_rub)} ₽</b>\n\n"
            f"<i>{budget_note}Предварительный расчёт по условному курсу "
            f"1 € = {WEBAPP_EUR_RUB_RATE:g} ₽. "
            "Точную стоимость уточнит менеджер.</i>"
        )
        _edit_screen(
            message.chat.id,
            int(session["message_id"]),
            result_text,
            result_menu(),
        )
        calculator_sessions.pop(user_id, None)


def run_polling() -> None:
    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30,
            )
        except KeyboardInterrupt:
            logger.info("Остановка Hybrid showcase-бота по Ctrl+C")
            bot.stop_polling()
            return
        except (ApiTelegramException, OSError):
            logger.exception("Ошибка соединения с Telegram. Повтор через 5 секунд.")
            time.sleep(5)


if __name__ == "__main__":
    init_db()
    configure_commands()
    logger.info("Hybrid showcase-бот запущен")
    run_polling()
