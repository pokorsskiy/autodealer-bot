---
name: ui-designer
description: Шаблоны и правила верстки сообщений и клавиатур для Telegram бота (HTML форматирование, Inline и Reply меню).
---

# Навык UI/UX дизайна Telegram-ботов

## 1. Правила HTML-форматирования сообщений
* **Всегда экранировать вводимый текст пользователя**:
  ```python
  import html
  safe_text = html.escape(user_input)
  ```
* **Разрешенные теги Telegram HTML**:
  * `<b>Жирный текст</b>`
  * `<i>Курсив</i>`
  * `<code>Моноширинный текст (код/ID)</code>`
  * `<pre>Многострочный код</pre>`
  * `<a href="https://t.me/dealer_auto">Ссылка</a>`

## 2. Шаблоны клавиатур (`keyboards.py`)

### А. Inline-кнопки по сетке (2 кнопки в ряд):
```python
def get_grid_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚗 Каталог", callback_data="catalog"),
        types.InlineKeyboardButton("🧮 Калькулятор", callback_data="calc"),
        types.InlineKeyboardButton("📞 Связаться", url="https://t.me/dealer_auto")
    )
    return markup
```

### Б. Reply-клавиатура (кнопка отправки телефона):
```python
def get_phone_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    return markup
```

## 3. Карточки товаров / Автомобилей
При формировании карточек авто в тексте использовать структурированный эмодзи-список:
```
🚘 <b>BMW X5 xDrive30d (2022)</b>

💰 <b>Цена:</b> 8 500 000 ₽
📍 <b>Статус:</b> В наличии (Иркутск)
⚙️ <b>Пробег:</b> 25 000 км | 3.0 Дизель (249 л.с.)

👇 Нажмите кнопку ниже для консультации:
```
