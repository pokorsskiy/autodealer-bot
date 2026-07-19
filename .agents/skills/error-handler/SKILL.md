---
name: error-handler
description: Обработка исключений, предотвращение падений бота и автоматическая отправка логов ошибок администратору.
---

# Навык обработчика ошибок и отказоустойчивости

## 1. Безопасный вызов Telegram API (`try-except`)
Всегда обрабатывать возможные сетевые сбои или блокировки со стороны Telegram (`ApiTelegramException`):

```python
from telebot.apihelper import ApiTelegramException

try:
    bot.send_message(chat_id, text)
except ApiTelegramException as e:
    if e.error_code == 403:
        # Пользователь заблокировал бота
        log_db("USER_BLOCKED", f"User {chat_id} blocked the bot")
    else:
        log_error("send_message", e)
```

## 2. Глобальный логгер ошибок с уведомлением админа
Если в хэндлере произошла непредвиденная ошибка, бот оповещает пользователя вежливым сообщением и отправляет админу стек-трейс:

```python
import traceback

def safe_handler(func):
    """Декоратор для безопасного выполнения хэндлеров"""
    def wrapper(message, *args, **kwargs):
        try:
            return func(message, *args, **kwargs)
        except Exception as e:
            err_tb = traceback.format_exc()
            log_error(func.__name__, err_tb)
            bot.send_message(message.chat.id, "❌ Произошла ошибка. Мы уже устраняем её!")
            # Уведомление админу
            bot.send_message(YOUR_CHAT_ID, f"⚠️ <b>Ошибка в handler '{func.__name__}':</b>\n<code>{err_tb[:1000]}</code>", parse_mode='HTML')
    return wrapper
```
