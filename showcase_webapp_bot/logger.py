"""Отказоустойчивость обработчиков Web App-бота."""

import html
import logging
import traceback
from functools import wraps

from telebot.apihelper import ApiTelegramException

from config import YOUR_CHAT_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("showcase_webapp_bot")


def safe_handler(bot):
    def decorator(handler):
        @wraps(handler)
        def wrapper(message, *args, **kwargs):
            try:
                return handler(message, *args, **kwargs)
            except Exception:
                details = traceback.format_exc()
                logger.exception("Ошибка в %s", handler.__name__)
                try:
                    bot.send_message(message.chat.id, "❌ Не удалось обработать заявку. Попробуйте ещё раз.")
                except ApiTelegramException:
                    pass
                if YOUR_CHAT_ID:
                    try:
                        bot.send_message(YOUR_CHAT_ID, f"⚠️ <b>Web App ошибка</b>\n<pre>{html.escape(details[-1500:])}</pre>", parse_mode="HTML")
                    except ApiTelegramException:
                        pass
        return wrapper
    return decorator
