# Hybrid showcase

Бот объединяет быстрые действия обычного Telegram showcase и опубликованный
Web App-каталог. В чате доступны калькулятор, FAQ, ссылки и заявка через системную
отправку контакта. Каталог, его калькулятор и подробная форма заявки открываются
в Web App.

Скопируйте `.env.example` в `.env` и заполните как минимум `BOT_TOKEN`,
`YOUR_CHAT_ID` и публичный HTTPS-адрес `WEB_APP_URL`. Остальные ссылки и параметры
калькулятора необязательны.

Для `WEB_APP_URL` можно использовать тот же опубликованный интерфейс и Flask-сервер,
что у `showcase_webapp_bot`: данные формы будут отправлены тому Telegram-боту,
из меню которого пользователь открыл Web App.

Запуск из папки `showcase_hybrid_bot`:

```powershell
python bot.py
```

Проверка:

```powershell
python -m unittest -v test_bot.py
python check_project.py
```
