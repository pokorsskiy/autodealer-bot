---
name: ui-designer
description: Проектирование интерфейсов Telegram-ботов и Telegram Web Apps: HTML-сообщения, inline/reply-клавиатуры, мобильные формы, карточки автомобилей и безопасная передача данных.
---

# Дизайн Telegram-интерфейсов и Web App

## 1. Telegram-сообщения

- Пользовательский ввод перед `parse_mode='HTML'` всегда экранировать через `html.escape`.
- Использовать только поддерживаемые Telegram HTML-теги: `<b>`, `<i>`, `<code>`, `<pre>`, `<a>`.
- Тексты кнопок делать короткими и однозначными.
- Для callback-кнопок использовать стабильные значения `callback_data` и вызывать `answer_callback_query`.

## 2. Клавиатуры

Хранить фабрики клавиатур в `keyboards.py`.

```python
def get_grid_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚗 Каталог", callback_data="catalog"),
        types.InlineKeyboardButton("🧮 Калькулятор", callback_data="calc"),
        types.InlineKeyboardButton("📞 Связаться", url="https://t.me/dealer_auto"),
    )
    return markup
```

Для телефона использовать системную кнопку контакта:

```python
def get_phone_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    return markup
```

## 3. Telegram Web App

- Публиковать Web App только по HTTPS.
- Подключать `https://telegram.org/js/telegram-web-app.js`.
- При старте вызывать `Telegram.WebApp.ready()` и, если нужно, `expand()`.
- Не хранить токены и секреты в HTML, CSS или JavaScript.
- Перед `sendData` проверять обязательные поля и ограничивать их длину.
- Отправлять данные в JSON через `Telegram.WebApp.sendData(JSON.stringify(payload))`.
- На стороне бота повторно валидировать и ограничивать все поля.
- Не считать данные из браузера доверенными только потому, что они пришли из Web App.
- Учитывать мобильную ширину Telegram: удобные поля, крупные кнопки, контрастный текст и отсутствие горизонтального скролла.

## 4. Карточки автомобилей

Использовать единый формат карточки:

```text
🚘 <b>BMW X5 xDrive30d (2022)</b>

💰 <b>Цена:</b> 8 500 000 ₽
📍 <b>Статус:</b> В наличии
⚙️ <b>Пробег:</b> 25 000 км | 3.0 Дизель

👇 Нажмите кнопку ниже для консультации:
```

## 5. Проверка интерфейса

- Проверять пустые, слишком длинные и специальные значения.
- Проверять форму на мобильной ширине.
- Проверять, что выбор карточки действительно попадает в поле заявки.
- Проверять поведение при открытии сайта вне Telegram: показывать понятное сообщение, не падать.
