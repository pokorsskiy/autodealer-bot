"""Безопасное логирование и обработка ошибок Web App-бота."""

import logging
from functools import wraps

from telebot.apihelper import ApiTelegramException

from config import YOUR_CHAT_ID


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("showcase_webapp_bot")


def safe_handler(bot):
    """Не допускает падения обработчиков и не раскрывает детали ошибок в Telegram."""
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, *args, **kwargs):
            try:
                return handler(event, *args, **kwargs)
            except Exception:
                logger.exception("Ошибка в обработчике %s", handler.__name__)
                chat = getattr(event, "chat", None)
                if chat is None and getattr(event, "message", None) is not None:
                    chat = event.message.chat

                try:
                    if chat:
                        bot.send_message(chat.id, "❌ Не удалось выполнить действие. Попробуйте ещё раз.")
                except ApiTelegramException:
                    logger.warning("Не удалось уведомить пользователя об ошибке")

                if YOUR_CHAT_ID and (chat is None or chat.id != YOUR_CHAT_ID):
                    try:
                        bot.send_message(
                            YOUR_CHAT_ID,
                            "⚠️ В Web App-боте произошла ошибка. Подробности сохранены в локальном логе.",
                        )
                    except ApiTelegramException:
                        logger.warning("Не удалось уведомить менеджера об ошибке")
        return wrapper
    return decorator
