"""Showcase обычного Telegram-бота для автомобильного бизнеса."""

import html

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

from calculator import AGE_LABELS, calculate_total_from_rub
from config import (
    DELIVERY_COST_RUB,
    EUR_RUB_RATE,
    OTHER_COSTS_RUB,
    TOKEN,
    YOUR_CHAT_ID,
)
from keyboards import (
    age_menu,
    back_to_menu,
    calculator_cancel,
    community_menu,
    faq_answer_menu,
    faq_menu,
    main_menu,
    order_cancel,
    order_confirmation_menu,
    result_menu,
    reviews_menu,
    socials_menu,
)
from logger import logger, safe_handler


if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Скопируйте .env.example в .env и укажите токен.")

bot = telebot.TeleBot(TOKEN)
calculator_sessions: dict[int, dict[str, object]] = {}
order_sessions: dict[int, dict[str, int]] = {}
last_calculations: dict[int, str] = {}

MAIN_TEXT = (
    "👋 <b>Добро пожаловать{name}!</b>\n\n"
    "Здесь можно предварительно рассчитать стоимость автомобиля, получить ответы "
    "на частые вопросы и связаться с менеджером."
)

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
    "manager": "Контакт менеджера",
    "reviews": "Ссылка на отзывы",
    "community": "Ссылка на общий чат",
    "telegram_channel": "Ссылка на Telegram-канал",
    "vk": "Ссылка на ВКонтакте",
    "youtube": "Ссылка на YouTube",
}


def _main_text(first_name: str | None = None) -> str:
    name = f", {html.escape(first_name)}" if first_name else ""
    return MAIN_TEXT.format(name=name)


def _format_rub(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_eur(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _manager_lead_text(
    user: types.User,
    request_text: str,
    calculation_summary: str | None,
) -> str:
    full_name = html.escape(
        " ".join(filter(None, [getattr(user, "first_name", None), getattr(user, "last_name", None)]))
        or "Не указано"
    )
    username_value = getattr(user, "username", None)
    username = f"@{html.escape(username_value)}" if username_value else "не указан"
    profile = f'<a href="tg://user?id={user.id}">{full_name}</a>'
    text = (
        "🟠 <b>Новая заявка на заказ автомобиля</b>\n\n"
        f"👤 Клиент: {profile}\n"
        f"💬 Username: {username}\n"
        f"🆔 Telegram ID: <code>{user.id}</code>\n\n"
        f"📝 <b>Запрос клиента</b>\n{html.escape(request_text)}"
    )
    if calculation_summary:
        text += f"\n\n🧮 <b>Последний расчёт клиента</b>\n{calculation_summary}"
    return text


def _answer_callback(call: types.CallbackQuery, text: str | None = None) -> None:
    try:
        bot.answer_callback_query(call.id, text=text)
    except ApiTelegramException as error:
        if error.error_code == 400:
            logger.info("Устаревший callback %s: %s", call.id, error.description)
        else:
            raise


def _edit_screen(
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: types.InlineKeyboardMarkup,
    parse_mode: str | None = "HTML",
) -> None:
    try:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    except ApiTelegramException as error:
        description = (error.description or "").lower()
        if error.error_code == 400 and "message is not modified" in description:
            return
        raise


def _edit_callback_screen(
    call: types.CallbackQuery,
    text: str,
    reply_markup: types.InlineKeyboardMarkup,
) -> None:
    _edit_screen(call.message.chat.id, call.message.message_id, text, reply_markup)


def _edit_calculator_screen(
    message: types.Message,
    session: dict[str, object],
    text: str,
    reply_markup: types.InlineKeyboardMarkup,
) -> None:
    _edit_screen(
        message.chat.id,
        int(session["message_id"]),
        text,
        reply_markup,
    )


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
    if not normalized.isdigit():
        return None
    return int(normalized)


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


def _send_main_menu(chat_id: int, first_name: str | None = None) -> None:
    """Убирает старую reply-клавиатуру и создаёт новое inline-меню."""
    cleanup_message = bot.send_message(
        chat_id,
        "Клавиатура обновлена.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.send_message(
        chat_id,
        _main_text(first_name),
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
    try:
        bot.delete_message(chat_id, cleanup_message.message_id)
    except ApiTelegramException:
        logger.warning("Не удалось удалить техническое сообщение: chat_id=%s", chat_id)


def configure_commands() -> None:
    """Показывает кнопку меню Telegram с единственной командой /start."""
    try:
        bot.set_my_commands(
            [types.BotCommand("start", "Запустить бота")]
        )
        bot.set_chat_menu_button(menu_button=types.MenuButtonCommands(type="commands"))
    except ApiTelegramException:
        logger.exception("Не удалось обновить меню команд Telegram")


@bot.message_handler(commands=["start"])
@safe_handler(bot)
def start(message: types.Message) -> None:
    calculator_sessions.pop(message.from_user.id, None)
    order_sessions.pop(message.from_user.id, None)
    _send_main_menu(message.chat.id, message.from_user.first_name)


@bot.callback_query_handler(func=lambda call: True)
@safe_handler(bot)
def handle_callback(call: types.CallbackQuery) -> None:
    data = call.data or ""
    user_id = call.from_user.id

    if data.startswith("stub:"):
        key = data.split(":", 1)[1]
        label = STUB_LABELS.get(key, "Ссылка")
        _answer_callback(call, f"{label} будет добавлена позже.")
        return

    _answer_callback(call)

    if data == "menu":
        calculator_sessions.pop(user_id, None)
        _edit_callback_screen(call, _main_text(call.from_user.first_name), main_menu())
        return

    if data == "manager":
        _edit_callback_screen(
            call,
            "📞 <b>Связаться с менеджером</b>\n\nКонтакт менеджера будет добавлен позже.",
            back_to_menu(),
        )
        return

    if data == "order:menu":
        _edit_screen(
            call.message.chat.id,
            call.message.message_id,
            getattr(call.message, "text", None)
            or "✅ Заявка отправлена менеджеру. Он свяжется с вами в Telegram.",
            reply_markup=None,
            parse_mode=None,
        )
        _send_main_menu(call.message.chat.id, call.from_user.first_name)
        return

    if data == "order":
        order_message = bot.send_message(
            call.message.chat.id,
            "🟠 <b>Заявка на автомобиль</b>\n\n"
            "Напишите, какой автомобиль вы ищете: марку, модель, бюджет, год, "
            "пробег или другие пожелания. Контактные данные вводить не нужно.",
            parse_mode="HTML",
            reply_markup=order_cancel(),
        )
        order_sessions[user_id] = {"message_id": order_message.message_id}
        return

    if data == "order:cancel":
        order_sessions.pop(user_id, None)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except ApiTelegramException as error:
            if error.error_code == 400:
                logger.info("Сообщение заявки уже удалено: %s", call.message.message_id)
            else:
                raise
        return

    if data == "calculator":
        calculator_message = bot.send_message(
            call.message.chat.id,
            "🧮 <b>Предварительный расчёт</b>\n\n"
            "Шаг 1 из 3. Введите стоимость автомобиля в рублях, например: "
            "<code>2 500 000</code> или <code>2 500 000 ₽</code>.",
            parse_mode="HTML",
            reply_markup=calculator_cancel(),
        )
        calculator_sessions[user_id] = {
            "step": "price",
            "message_id": calculator_message.message_id,
        }
        return

    if data == "calc:cancel":
        calculator_sessions.pop(user_id, None)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except ApiTelegramException as error:
            if error.error_code == 400:
                logger.info("Сообщение калькулятора уже удалено: %s", call.message.message_id)
            else:
                raise
        return

    if data.startswith("calc:age:"):
        session = calculator_sessions.get(user_id)
        if not session or session.get("step") != "age":
            _edit_callback_screen(
                call,
                "Расчёт устарел. Начните заново.",
                back_to_menu(),
            )
            return
        age = data.removeprefix("calc:age:")
        if age not in AGE_LABELS:
            return
        session["age"] = age
        session["step"] = "engine"
        _edit_callback_screen(
            call,
            "🧮 <b>Предварительный расчёт</b>\n\n"
            "Шаг 3 из 3. Введите объём двигателя в литрах, например: "
            "<code>2.0</code> или <code>1,6 л</code>.",
            calculator_cancel(),
        )
        return

    if data == "reviews":
        _edit_callback_screen(
            call,
            "⭐ <b>Отзывы клиентов</b>\n\nГруппа отзывов будет добавлена позже.",
            back_to_menu(),
        )
        return

    if data == "community":
        _edit_callback_screen(
            call,
            "💬 <b>Общий чат</b>\n\nОбщий чат будет добавлен позже.",
            back_to_menu(),
        )
        return

    if data == "faq":
        _edit_callback_screen(
            call,
            "❓ <b>Популярные вопросы</b>\n\nВыберите вопрос:",
            faq_menu(),
        )
        return

    if data.startswith("faq:"):
        answer = FAQ_ANSWERS.get(data.split(":", 1)[1])
        if answer:
            _edit_callback_screen(call, answer, faq_answer_menu())
        return

    if data == "socials":
        _edit_callback_screen(
            call,
            "🌐 <b>Другие соцсети</b>\n\nВыберите площадку:",
            socials_menu(),
        )


@bot.message_handler(content_types=["text"])
@safe_handler(bot)
def handle_text(message: types.Message) -> None:
    order_session = order_sessions.get(message.from_user.id)
    if order_session:
        request_text = (message.text or "").strip()
        if not 3 <= len(request_text) <= 1_500:
            bot.send_message(
                message.chat.id,
                "Опишите пожелания к автомобилю текстом от 3 до 1 500 символов.",
            )
            return
        if not YOUR_CHAT_ID:
            logger.warning("Заявка не отправлена: не задан YOUR_CHAT_ID")
            bot.send_message(
                message.chat.id,
                "⚠️ Заявки временно недоступны. Попробуйте связаться с менеджером позже.",
            )
            return

        bot.send_message(
            YOUR_CHAT_ID,
            _manager_lead_text(
                message.from_user,
                request_text,
                last_calculations.get(message.from_user.id),
            ),
            parse_mode="HTML",
        )
        try:
            bot.delete_message(message.chat.id, order_session["message_id"])
        except ApiTelegramException as error:
            if error.error_code != 400:
                raise
            logger.info("Сообщение формы заявки уже удалено: %s", order_session["message_id"])
        order_sessions.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            "✅ Заявка отправлена менеджеру. Он свяжется с вами в Telegram.",
            reply_markup=order_confirmation_menu(),
        )
        return

    session = calculator_sessions.get(message.from_user.id)
    if not session:
        _send_main_menu(message.chat.id, message.from_user.first_name)
        return

    if session.get("step") == "price":
        price_rub = _parse_rub_price(message.text or "")
        if price_rub is None or not 50_000 <= price_rub <= 50_000_000:
            bot.send_message(
                message.chat.id,
                "Введите стоимость от 50 000 до 50 000 000 ₽, например: <code>2 500 000</code>.",
                parse_mode="HTML",
            )
            return
        session["car_price_rub"] = price_rub
        session["step"] = "age"
        _edit_calculator_screen(
            message,
            session,
            "🧮 <b>Предварительный расчёт</b>\n\n"
            "Шаг 2 из 3. Выберите возраст автомобиля:",
            age_menu(),
        )
        return

    if session.get("step") == "engine":
        engine_liters = _parse_engine_liters(message.text or "")
        if engine_liters is None or not 0.5 <= engine_liters <= 10:
            bot.send_message(
                message.chat.id,
                "Введите объём двигателя от 0.5 до 10 л, например: <code>2.0</code> или <code>1,6 л</code>.",
                parse_mode="HTML",
            )
            return

        engine_cc = round(engine_liters * 1000)
        age = str(session["age"])
        calculation = calculate_total_from_rub(
            car_price_rub=int(session["car_price_rub"]),
            age=age,
            engine_cc=engine_cc,
            eur_rub_rate=EUR_RUB_RATE,
            delivery_rub=DELIVERY_COST_RUB,
            other_costs_rub=OTHER_COSTS_RUB,
        )
        result_text = (
            "🧮 <b>Ориентировочный расчёт</b>\n\n"
            f"🚘 Стоимость автомобиля: <b>{_format_rub(calculation.car_price_rub)} ₽</b>\n"
            f"💱 Для расчёта: <b>{_format_eur(calculation.car_price_eur)} €</b>\n"
            f"🛃 Таможенная пошлина: <b>{_format_rub(calculation.duty_rub)} ₽</b>\n"
            f"🚚 Доставка: <b>{_format_rub(calculation.delivery_rub)} ₽</b>\n"
            f"📄 Прочие расходы: <b>{_format_rub(calculation.other_costs_rub)} ₽</b>\n\n"
            f"Итого ориентировочно: <b>{_format_rub(calculation.total_rub)} ₽</b>\n\n"
            f"<i>Курс расчёта: 1 € = {EUR_RUB_RATE:g} ₽. "
            f"Возраст: {AGE_LABELS[age]}, двигатель: {engine_liters:.1f} л ({_format_rub(engine_cc)} см³). "
            "Расчёт предварительный: итог зависит от курса, характеристик автомобиля, "
            "утилизационного сбора и расходов на оформление.</i>"
        )
        _edit_calculator_screen(message, session, result_text, result_menu())
        last_calculations[message.from_user.id] = (
            f"Стоимость: {_format_rub(calculation.car_price_rub)} ₽\n"
            f"Возраст: {AGE_LABELS[age]}\n"
            f"Двигатель: {engine_liters:.1f} л ({_format_rub(engine_cc)} см³)\n"
            f"Итого: {_format_rub(calculation.total_rub)} ₽"
        )
        calculator_sessions.pop(message.from_user.id, None)


def run_polling() -> None:
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
    except KeyboardInterrupt:
        logger.info("Остановка Telegram showcase-бота по Ctrl+C")
    finally:
        bot.stop_polling()


if __name__ == "__main__":
    configure_commands()
    logger.info("Telegram showcase-бот запущен")
    run_polling()
