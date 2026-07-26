"""Безопасное логирование ошибок гибридного showcase-бота."""

import logging
from functools import wraps

from telebot.apihelper import ApiTelegramException

from config import YOUR_CHAT_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("showcase_hybrid_bot")


def safe_handler(bot):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, *args, **kwargs):
            try:
                return handler(event, *args, **kwargs)
            except Exception:
                logger.exception("Ошибка в обработчике %s", handler.__name__)
                message = getattr(event, "message", event)
                chat_id = getattr(getattr(message, "chat", None), "id", None)
                if chat_id is not None:
                    try:
                        bot.send_message(chat_id, "❌ Временная ошибка. Попробуйте ещё раз.")
                    except ApiTelegramException:
                        logger.exception("Не удалось уведомить пользователя")
                if YOUR_CHAT_ID and YOUR_CHAT_ID != chat_id:
                    try:
                        bot.send_message(
                            YOUR_CHAT_ID,
                            "⚠️ В Hybrid-боте произошла ошибка. Подробности сохранены в локальном логе.",
                        )
                    except ApiTelegramException:
                        logger.exception("Не удалось уведомить администратора")
        return wrapper
    return decorator
