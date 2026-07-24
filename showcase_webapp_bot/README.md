# Web App showcase

Бот открывает каталог и форму заявки внутри Telegram Web App.

Заполните в локальном `.env` значения `BOT_TOKEN`, `YOUR_CHAT_ID`, `WEB_APP_URL`
и при необходимости `DB_NAME`. Адрес `WEB_APP_URL` должен быть публичным HTTPS URL,
по которому опубликовано содержимое папки `web/`.

Запуск:

```powershell
python bot.py
```
