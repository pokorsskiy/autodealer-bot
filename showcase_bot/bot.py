"""
Главный исполняемый файл Telegram Бота-Продавца (Showcase Bot).
Переведен на архитектуру Telegram Web App.
"""

import html
import os
import sys
import json
from datetime import datetime
import telebot
from telebot import types

# Обеспечиваем правильный импорт локальных модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TOKEN, YOUR_CHAT_ID, WEB_APP_URL
from keyboards import get_webapp_keyboard

bot = telebot.TeleBot(TOKEN)


# ===================== УВЕДОМЛЕНИЯ АДМИНИСТРАТОРУ =====================
def notify_admin_about_web_app_lead(user: types.User, name: str, phone: str, interest: str, notes: str):
    """Отправка уведомления владельцу о новой заявке из Web App"""
    safe_user_first_name = html.escape(user.first_name or "Без имени")
    username_str = f"@{user.username}" if user.username else "Не указан"
    safe_name = html.escape(name)
    safe_phone = html.escape(phone)
    safe_interest = html.escape(interest)
    safe_notes = html.escape(notes) if notes else "Нет комментария"

    text = (
        f"🔥 <b>НОВАЯ ЗАЯВКА ИЗ WEB APP!</b>\n\n"
        f"👤 <b>Имя в Web App:</b> {safe_name}\n"
        f"📞 <b>Телефон:</b> {safe_phone}\n"
        f"💎 <b>Выбранный интерес:</b> {safe_interest}\n"
        f"📝 <b>Комментарий:</b> <i>{safe_notes}</i>\n\n"
        f"⚙️ <b>Аккаунт Telegram:</b>\n"
        f"• Имя: {safe_user_first_name}\n"
        f"• Username: {username_str}\n"
        f"• ID: <code>{user.id}</code>\n"
        f"📅 <b>Дата заявки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    try:
        bot.send_message(YOUR_CHAT_ID, text, parse_mode='HTML')
        print(f"[ADMIN NOTIFY] Заявка из Web App от {user.id} ({safe_name}) успешно отправлена админу.")
    except Exception as e:
        print(f"[ERROR] Ошибка отправки уведомления админу: {e}")


# ===================== КОМАНДЫ =====================
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    """Приветственное сообщение и вывод кнопки Web App"""
    user = message.from_user
    print(f"[MSG] {user.id} (@{user.username}): {message.text}")

    if not WEB_APP_URL:
        warning_text = (
            "⚠️ <b>Бот запущен, но Web App URL не настроен!</b>\n\n"
            "Пожалуйста, укажите переменную <code>WEB_APP_URL</code> в файле <code>.env</code> showcase бота, "
            "чтобы презентация работала."
        )
        bot.send_message(message.chat.id, warning_text, parse_mode='HTML')
        print(f"[WARNING] Пользователь {user.id} запустил бота, но WEB_APP_URL пуст!")
        return

    safe_name = html.escape(user.first_name or "Друг")
    text = (
        f"👋 <b>Привет, {safe_name}!</b>\n\n"
        f"🤖 Добро пожаловать в презентацию <b>Telegram-бота для Автодилеров и Автоподборщиков</b>!\n\n"
        f"Теперь вся наша презентация работает в формате интерактивного <b>Web App (Mini App)</b> прямо внутри Telegram!\n\n"
        f"• 🚗 Полноценный каталог автомобилей\n"
        f"• 🧮 Онлайн-калькулятор доставки и растаможки авто под ключ в РФ\n"
        f"• 💎 Описание тарифов и возможностей\n\n"
        f"👇 <b>Нажмите кнопку ниже, чтобы открыть презентацию:</b>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode='HTML',
        reply_markup=get_webapp_keyboard(WEB_APP_URL)
    )


# ===================== ОБРАБОТКА ДАННЫХ ИЗ WEB APP =====================
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message: types.Message):
    """Обработчик входящих данных от Telegram Web App"""
    user = message.from_user
    print(f"[WEB APP DATA] Получены данные от {user.id} (@{user.username})")

    try:
        data = json.loads(message.web_app_data.data)
        name = data.get('name', 'Не указано')
        phone = data.get('phone', 'Не указано')
        interest = data.get('interest', 'Не указано')
        notes = data.get('notes', '')

        # Отправка уведомления администратору напрямую без сохранения в БД
        notify_admin_about_web_app_lead(user, name, phone, interest, notes)

        thanks_text = (
            f"🎉 <b>Спасибо за заявку, {html.escape(name)}!</b>\n\n"
            f"Мы получили ваши контакты (<code>{html.escape(phone)}</code>) по направлению: "
            f"<b>{html.escape(interest)}</b>.\n\n"
            f"Наш менеджер уже уведомлен и свяжется с вами в ближайшее время! 🚀"
        )
        bot.send_message(message.chat.id, thanks_text, parse_mode='HTML')

    except json.JSONDecodeError:
        print(f"[ERROR] Ошибка парсинга JSON от Web App")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке данных из Web App.")
    except Exception as e:
        print(f"[ERROR] Ошибка в обработчике web_app_data: {e}")
        bot.send_message(message.chat.id, "❌ Не удалось обработать вашу заявку.")


@bot.message_handler(func=lambda msg: True)
def handle_other_messages(message: types.Message):
    """Заглушка на текстовые сообщения"""
    if not WEB_APP_URL:
        start(message)
        return
        
    bot.send_message(
        message.chat.id,
        "💡 Нажмите кнопку <b>«Открыть презентацию (Web App)»</b> ниже, чтобы запустить интерактивное меню презентации.",
        reply_markup=get_webapp_keyboard(WEB_APP_URL)
    )


# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    if not WEB_APP_URL:
        print("[WARNING] Внимание: Переменная WEB_APP_URL не задана в .env!")
    else:
        print(f"[INFO] Web App URL настроен на: {WEB_APP_URL}")

    # Попытка установить кнопку меню Web App
    try:
        if WEB_APP_URL:
            bot.set_chat_menu_button(
                menu_button=types.MenuButtonWebApp(
                    text="Презентация 🚀",
                    web_app=types.WebAppInfo(url=WEB_APP_URL)
                )
            )
            print("[INFO] Кнопка меню (Menu Button) Web App успешно установлена в чате.")
    except Exception as e:
        print(f"[WARNING] Не удалось настроить Menu Button Web App: {e}")

    print("[INFO] Бот-Продавец Showcase запущен на Web App.")
    bot.infinity_polling(skip_pending=True)

