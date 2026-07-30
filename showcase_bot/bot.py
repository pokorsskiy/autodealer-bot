"""Главный файл Telegram-бота-витрины Dealer Auto."""

import html
import sys
import time
from functools import wraps
from pathlib import Path

import telebot
from telebot.apihelper import ApiTelegramException

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from showcase_bot.config import (
    BOT_TOKEN,
    DB_NAME,
    MENU_COVER_FILE_ID,
    SHOWCASES,
    SUPPORT_URL,
    YOUR_CHAT_ID,
)
from showcase_bot.database import init_db, save_lead
from showcase_bot.keyboards import (
    get_catalog_keyboard,
    get_cancel_keyboard,
    get_main_keyboard,
    get_showcase_keyboard,
    get_support_keyboard,
)
from showcase_bot.logger import logger


if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Добавьте его в showcase_bot/.env.")

bot = telebot.TeleBot(BOT_TOKEN)
awaiting_lead_from: set[int] = set()
SHOWCASES_BY_KEY = {item["key"]: item for item in SHOWCASES}
MENU_COVER_PATH = Path(__file__).resolve().parent / "menu-cover.jpg"
_menu_cover_file_id_logged = False
MAIN_MENU_TEXT = (
    "<b>Autobot — боты для авто-бизнеса</b>\n\n"
    "Покажу готовые решения и помогу собрать бота под вашу задачу."
)


def safe_handler(handler):
    """Логирует ошибки обработчиков и не раскрывает детали пользователю."""
    @wraps(handler)
    def wrapper(event, *args, **kwargs):
        try:
            return handler(event, *args, **kwargs)
        except Exception:
            logger.exception("Ошибка в обработчике %s", handler.__name__)
    return wrapper


def send_main_menu(chat_id: int) -> None:
    """Отправляет меню через Telegram file_id, если он уже сохранён."""
    global _menu_cover_file_id_logged

    try:
        if MENU_COVER_FILE_ID:
            bot.send_photo(
                chat_id,
                MENU_COVER_FILE_ID,
                caption=MAIN_MENU_TEXT,
                parse_mode="HTML",
                reply_markup=get_main_keyboard(),
            )
            return

        with MENU_COVER_PATH.open("rb") as cover:
            sent_message = bot.send_photo(
                chat_id,
                cover,
                caption=MAIN_MENU_TEXT,
                parse_mode="HTML",
                reply_markup=get_main_keyboard(),
            )

        if not _menu_cover_file_id_logged and sent_message.photo:
            logger.info(
                "Добавьте в showcase_bot/.env: MENU_COVER_FILE_ID=%s",
                sent_message.photo[-1].file_id,
            )
            _menu_cover_file_id_logged = True
    except (OSError, ApiTelegramException):
        logger.exception("Не удалось отправить обложку главного меню")
        bot.send_message(
            chat_id,
            MAIN_MENU_TEXT,
            parse_mode="HTML",
            reply_markup=get_main_keyboard(),
        )


def show_main_menu(call: telebot.types.CallbackQuery) -> None:
    """Удаляет текущий экран и показывает главное меню с обложкой."""
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except ApiTelegramException as error:
        if error.error_code != 400:
            raise
    send_main_menu(call.message.chat.id)


def edit_screen(
    call: telebot.types.CallbackQuery,
    text: str,
    reply_markup: telebot.types.InlineKeyboardMarkup,
    parse_mode: str | None = None,
) -> None:
    """Обновляет экран бота в текущем сообщении."""
    if getattr(call.message, "content_type", "") == "photo":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except ApiTelegramException as error:
            if error.error_code != 400:
                raise
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
        return
    try:
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    except ApiTelegramException as error:
        description = (error.description or "").lower()
        if error.error_code == 400 and "message is not modified" in description:
            logger.debug("Экран уже открыт: chat_id=%s", call.message.chat.id)
            return
        raise


@bot.message_handler(commands=["start", "menu"])
@safe_handler
def start(message: telebot.types.Message) -> None:
    awaiting_lead_from.discard(message.from_user.id)
    send_main_menu(message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
@safe_handler
def handle_callback(call: telebot.types.CallbackQuery) -> None:
    try:
        bot.answer_callback_query(call.id)
    except ApiTelegramException as error:
        if error.error_code == 400:
            logger.info("Устаревший callback %s: %s", call.id, error.description)
        else:
            logger.warning("Не удалось подтвердить callback %s: %s", call.id, error)
    data = call.data

    if data == "menu":
        awaiting_lead_from.discard(call.from_user.id)
        show_main_menu(call)
        return

    if data == "catalog":
        edit_screen(
            call,
            "<b>Примеры готовых ботов</b>\n\nВыберите бота, чтобы узнать подробности.",
            get_catalog_keyboard(),
            parse_mode="HTML",
        )
        return

    if data.startswith("showcase:"):
        showcase = SHOWCASES_BY_KEY.get(data.split(":", 1)[1])
        if showcase:
            url_note = "" if showcase["url"] else "\n\n<i>Ссылка будет добавлена после публикации примера.</i>"
            edit_screen(
                call,
                f"<b>{html.escape(showcase['title'])}</b>\n\n"
                f"{html.escape(showcase['description'])}{url_note}",
                get_showcase_keyboard(showcase),
                parse_mode="HTML",
            )
        return

    if data == "lead:start":
        awaiting_lead_from.add(call.from_user.id)
        edit_screen(
            call,
            "Опишите задачу: какой бот нужен, что должен уметь и для кого он будет работать.\n\n"
            "Одним сообщением, до 2 000 символов.",
            get_cancel_keyboard(),
        )
        return

    if data == "lead:cancel":
        awaiting_lead_from.discard(call.from_user.id)
        show_main_menu(call)
        return

    if data == "support":
        text = (
            "Контакты доступны по кнопке ниже."
            if SUPPORT_URL
            else "Контакт поддержки пока не настроен. Оставьте заявку — мы свяжемся с вами."
        )
        edit_screen(call, text, get_support_keyboard())
        return

@bot.message_handler(content_types=["text"])
@safe_handler
def receive_lead(message: telebot.types.Message) -> None:
    user = message.from_user
    if user.id not in awaiting_lead_from:
        send_main_menu(message.chat.id)
        return

    description = (message.text or "").strip()
    if not description:
        bot.send_message(message.chat.id, "Опишите задачу текстом.")
        return
    if len(description) > 2000:
        bot.send_message(message.chat.id, "Сократите описание до 2 000 символов.")
        return

    lead_id = save_lead(DB_NAME, user.id, user.username, user.first_name, description)
    awaiting_lead_from.discard(user.id)

    if YOUR_CHAT_ID:
        username = f"@{user.username}" if user.username else "не указан"
        admin_text = (
            f"<b>Новая заявка №{lead_id}</b>\n\n"
            f"<b>Имя:</b> {html.escape(user.first_name or 'не указано')}\n"
            f"<b>Username:</b> {html.escape(username)}\n"
            f"<b>ID:</b> <code>{user.id}</code>\n\n"
            f"<b>Задача:</b>\n{html.escape(description)}"
        )
        try:
            bot.send_message(YOUR_CHAT_ID, admin_text, parse_mode="HTML")
        except ApiTelegramException:
            logger.exception("Заявка №%s сохранена, но не отправлена администратору", lead_id)

    bot.send_message(
        message.chat.id,
        "✅ Заявка принята. Скоро свяжемся с вами.",
    )
    send_main_menu(message.chat.id)


def run_polling() -> None:
    """Перезапускает polling после временных сетевых ошибок."""
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except (ApiTelegramException, OSError):
            logger.exception("Ошибка соединения с Telegram. Повтор через 5 секунд.")
            time.sleep(5)


if __name__ == "__main__":
    init_db(DB_NAME)
    logger.info("Бот-витрина запущен. База заявок: %s", DB_NAME)
    run_polling()
