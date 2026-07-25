"""Логирование и безопасное уведомление администратора об ошибках."""

import logging
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
                logger.exception("Ошибка в обработчике %s", handler.__name__)
                chat = getattr(message, "chat", None)
                if chat is None and getattr(message, "message", None) is not None:
                    chat = message.message.chat
                try:
                    if chat:
                        bot.send_message(chat.id, "❌ Не удалось выполнить действие. Попробуйте ещё раз.")
                except ApiTelegramException:
                    logger.warning("Не удалось сообщить пользователю об ошибке")

                if YOUR_CHAT_ID and (chat is None or chat.id != YOUR_CHAT_ID):
                    try:
                        bot.send_message(
                            YOUR_CHAT_ID,
                            "⚠️ В боте произошла ошибка. Подробности сохранены в локальном логе.",
                            parse_mode="HTML",
                        )
                    except ApiTelegramException:
                        logger.warning("Не удалось отправить отчёт администратору")
        return wrapper
    return decorator
