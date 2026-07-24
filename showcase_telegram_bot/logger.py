"""Логирование и безопасное уведомление администратора об ошибках."""

import html
import logging
import traceback
from functools import wraps

from telebot.apihelper import ApiTelegramException

from config import YOUR_CHAT_ID


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("showcase_telegram_bot")


def safe_handler(bot):
    """Не допускает падения polling из-за ошибки в пользовательском сценарии."""
    def decorator(handler):
        @wraps(handler)
        def wrapper(message, *args, **kwargs):
            try:
                return handler(message, *args, **kwargs)
            except Exception:
                error_details = traceback.format_exc()
                logger.exception("Ошибка в обработчике %s", handler.__name__)
                chat = getattr(message, "chat", None)
                if chat is None and getattr(message, "message", None) is not None:
                    chat = message.message.chat
                try:
                    if chat:
                        bot.send_message(chat.id, "❌ Не удалось выполнить действие. Попробуйте ещё раз.")
                except ApiTelegramException:
                    logger.warning("Не удалось сообщить пользователю об ошибке")

                if YOUR_CHAT_ID:
                    safe_error = html.escape(error_details[-1500:])
                    try:
                        bot.send_message(
                            YOUR_CHAT_ID,
                            f"⚠️ <b>Ошибка в {handler.__name__}</b>\n<pre>{safe_error}</pre>",
                            parse_mode="HTML",
                        )
                    except ApiTelegramException:
                        logger.warning("Не удалось отправить отчёт администратору")
        return wrapper
    return decorator
