# Dealer Auto Showcase Bot

Telegram-бот-витрина готовых решений для авто-бизнеса: каталог примеров, заявка на разработку и поддержка.

## Настройка

1. Скопируйте `.env.example` в `.env`.
2. Укажите `BOT_TOKEN` отдельного бота и `YOUR_CHAT_ID` владельца.
3. Заполните ссылки на опубликованные showcase-боты и поддержку.

## Запуск

```powershell
venv\Scripts\python.exe -m showcase_bot.bot
```

Заявки сохраняются в SQLite-файл, указанный в `DB_NAME`.
