"""Логирование ошибок гибридного showcase-бота."""

import html
import logging
import traceback
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
                details = traceback.format_exc()
                logger.exception("Ошибка в %s", handler.__name__)
                message = getattr(event, "message", event)
                try:
                    bot.send_message(message.chat.id, "❌ Временная ошибка. Попробуйте ещё раз.")
                except ApiTelegramException:
                    pass
                if YOUR_CHAT_ID:
                    try:
                        bot.send_message(YOUR_CHAT_ID, f"⚠️ <b>Hybrid ошибка</b>\n<pre>{html.escape(details[-1200:])}</pre>", parse_mode="HTML")
                    except ApiTelegramException:
                        pass
        return wrapper
    return decorator
