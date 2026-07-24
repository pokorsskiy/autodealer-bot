# Dealer Auto Bot

Репозиторий содержит основной Telegram-бот для учёта переходов из Instagram и
три самостоятельных демонстрационных сценария для автодилера.

## Состав проекта

- `autodealer_bot/` — основной бот: deep-link `?start=INSTA`, SQLite и команда `/db`.
- `showcase_telegram_bot/` — каталог и заявка в Telegram.
- `showcase_webapp_bot/` — каталог и заявка в Telegram Web App.
- `showcase_hybrid_bot/` — быстрые действия в Telegram и каталог в Web App.
- `showcase_telegram_bot/`, `showcase_webapp_bot/`, `showcase_hybrid_bot/` — независимые демонстрационные боты.

## Установка

Нужен Python 3.10 или новее.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Настройка основного бота

Создайте в корне файл `.env` и задайте:

```env
BOT_TOKEN=ваш_токен_из_BotFather
YOUR_CHAT_ID=ваш_числовой_chat_id
DB_NAME=data/instagram_users.db
```

Файл `.env` и SQLite-базы не попадают в Git. Не добавляйте токены в Python-код.

## Запуск

```powershell
python -m autodealer_bot.autodealer
```

Для Railway используется команда из `Procfile`.
