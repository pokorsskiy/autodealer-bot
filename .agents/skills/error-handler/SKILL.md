---
name: error-handler
description: Безопасная обработка исключений и сетевых ошибок в Telegram-ботах на pyTelegramBotAPI. Использовать при добавлении хэндлеров, уведомлений администратора, polling и callback/Web App-обработчиков.
---

# Обработка ошибок Telegram-бота

## 1. Безопасный вызов Telegram API

Оборачивать критичные вызовы Telegram API в `try/except` и отдельно обрабатывать `ApiTelegramException`:

```python
from telebot.apihelper import ApiTelegramException

try:
    bot.send_message(chat_id, text)
except ApiTelegramException as error:
    if error.error_code == 403:
        logger.warning("Пользователь заблокировал бота: %s", chat_id)
    else:
        logger.exception("Ошибка Telegram API")
```

Не отправлять пользователю стек-трейс, токены, содержимое `.env` или внутренние пути проекта.

## 2. Безопасный декоратор хэндлеров

Использовать единый контракт `safe_handler(bot)` для message- и callback-хэндлеров:

```python
import html
import traceback
from functools import wraps

from telebot.apihelper import ApiTelegramException


def safe_handler(bot):
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, *args, **kwargs):
            try:
                return handler(event, *args, **kwargs)
            except Exception:
                error_text = traceback.format_exc()
                logger.exception("Ошибка в обработчике %s", handler.__name__)
                message = getattr(event, "message", event)
                try:
                    bot.send_message(message.chat.id, "❌ Произошла ошибка. Попробуйте ещё раз.")
                except ApiTelegramException:
                    logger.exception("Не удалось уведомить пользователя")
                if YOUR_CHAT_ID:
                    try:
                        bot.send_message(
                            YOUR_CHAT_ID,
                            f"⚠️ <b>Ошибка в {html.escape(handler.__name__)}</b>\n"
                            f"<pre>{html.escape(error_text[-1500:])}</pre>",
                            parse_mode="HTML",
                        )
                    except ApiTelegramException:
                        logger.exception("Не удалось уведомить администратора")
        return wrapper
    return decorator
```

Перед отправкой ошибки администратору экранировать HTML через `html.escape` и ограничивать размер сообщения.

## 3. Обязательные правила

- Логировать исключение через `logger.exception`, сохраняя traceback локально.
- Не использовать пустые `except:`.
- Не скрывать ошибки базы данных и конфигурации без записи в лог.
- Для callback-событий получать чат через `event.message.chat`.
- После ошибки отправлять пользователю короткое безопасное сообщение.
- Для временных сетевых ошибок применять ограниченный retry только там, где это действительно нужно.
