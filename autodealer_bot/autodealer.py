"""
Главный файл Telegram бота Dealer Auto.
"""

import html
from datetime import datetime
import telebot
from telebot.apihelper import ApiTelegramException

from .config import PROJECT_ROOT, TOKEN, YOUR_CHAT_ID, DB_NAME
from .database import init_db, is_new_instagram_user, save_instagram_user
from .keyboards import get_main_keyboard
from .logger import log_msg, log_admin, log_error, log_system

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Укажите его в .env или переменных окружения.")

bot = telebot.TeleBot(TOKEN)
MENU_COVER_PATH = PROJECT_ROOT / "autodealer_bot" / "assets" / "menu-cover.jpg"


def send_main_menu(chat_id: int, welcome_text: str) -> None:
    """Отправляет главное меню с обложкой, а при ошибке — обычное сообщение."""
    try:
        with MENU_COVER_PATH.open("rb") as local_cover:
            bot.send_photo(
                chat_id,
                local_cover,
                caption=welcome_text,
                reply_markup=get_main_keyboard(),
            )
    except (OSError, ApiTelegramException) as error:
        log_error("send_main_menu", error)
        bot.send_message(chat_id, welcome_text, reply_markup=get_main_keyboard())


# ===================== УВЕДОМЛЕНИЯ =====================
def notify_new_client(message: telebot.types.Message):
    """Отправка уведомления администратору о новом клиенте из Instagram"""
    user = message.from_user
    safe_first_name = html.escape(user.first_name or "Без имени")
    username_str = f"@{user.username}" if user.username else "нет"

    text = (
        f"🔔 <b>НОВЫЙ КЛИЕНТ ИЗ INSTAGRAM!</b>\n\n"
        f"👤 Имя: {safe_first_name}\n"
        f"🔗 Username: {username_str}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📅 Когда: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"🔗 Перешёл по ссылке: ?start=INSTA"
    )
    
    try:
        bot.send_message(YOUR_CHAT_ID, text, parse_mode='HTML')
        log_admin(f"Уведомление о новом клиенте {user.id} успешно отправлено.")
    except Exception as e:
        log_error("notify_new_client", e)


# ===================== КОМАНДЫ =====================
@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    """Обработчик команды /start с поддержкой Deep-linking"""
    user = message.from_user
    log_msg(user.id, user.username, message.text)

    args = message.text.split()
    deep_link = args[1] if len(args) > 1 else ""

    if deep_link == "INSTA":
        if is_new_instagram_user(user.id):
            save_instagram_user(user.id, user.username, user.first_name)
            notify_new_client(message)
            welcome_text = "👋 Привет! Ты пришёл из Instagram\n\n👇 Вот полезные ссылки 👇"
        else:
            welcome_text = "👋 Привет! Ты уже был у нас\n\n👇 Вот полезные ссылки 👇"
    else:
        welcome_text = "👋 Привет! Это бот Dealer Auto\n\n👇 Вот полезные ссылки 👇"

    send_main_menu(message.chat.id, welcome_text)


@bot.message_handler(commands=['db'])
def send_db(message: telebot.types.Message):
    """Выгрузка файла базы данных администратору"""
    log_msg(message.from_user.id, message.from_user.username, "/db")
    
    if message.from_user.id == YOUR_CHAT_ID:
        try:
            with open(DB_NAME, 'rb') as db_file:
                bot.send_document(message.chat.id, db_file, caption="📂 Вот актуальная база instagram_users.db")
                log_admin("Файл базы данных отправлен админу.")
        except FileNotFoundError:
            bot.send_message(message.chat.id, "❌ База ещё не создана.")
        except Exception as e:
            log_error("send_db", e)
            bot.send_message(message.chat.id, f"❌ Ошибка отправки базы: {e}")
    else:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён.")


# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    init_db()
    log_system(f"Бот Dealer Auto запущен. База данных в {DB_NAME}")
    bot.infinity_polling(skip_pending=True)
