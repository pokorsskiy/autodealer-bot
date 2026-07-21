"""
Главный исполняемый файл Telegram Бота-Продавца (Showcase Bot).
Предназначен для демонстрации возможностей системы автодилерам и сбора лидов.
"""

import html
import os
import sys
from datetime import datetime
import telebot
from telebot import types

# Обеспечиваем правильный импорт локальных модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TOKEN, YOUR_CHAT_ID, DB_NAME
from database import init_db, save_or_update_lead, update_lead_contact, get_lead
from keyboards import (
    get_main_showcase_keyboard,
    get_demo_keyboard,
    get_tariffs_keyboard,
    get_back_keyboard,
    get_contact_reply_keyboard
)

bot = telebot.TeleBot(TOKEN)

# Хранение текущего выбранного тарифа для каждого пользователя
user_selected_tariffs = {}


# ===================== УВЕДОМЛЕНИЯ АДМИНИСТРАТОРУ =====================
def notify_admin_about_lead(user: types.User, phone: str, interest: str):
    """Отправка уведомления владельцу о новой заявке на покупку бота"""
    safe_first_name = html.escape(user.first_name or "Без имени")
    username_str = f"@{user.username}" if user.username else "Не указан"
    safe_phone = html.escape(phone)
    safe_interest = html.escape(interest)

    text = (
        f"🔥 <b>НОВАЯ ЗАЯВКА НА ПОКУПКУ БОТА!</b>\n\n"
        f"👤 <b>Имя:</b> {safe_first_name}\n"
        f"🔗 <b>Username:</b> {username_str}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"📞 <b>Телефон:</b> {safe_phone}\n"
        f"💎 <b>Выбранный тариф/Интерес:</b> {safe_interest}\n"
        f"📅 <b>Дата заявки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    try:
        bot.send_message(YOUR_CHAT_ID, text, parse_mode='HTML')
        print(f"[ADMIN NOTIFY] Заявка от {user.id} ({safe_interest}) успешно отправлена админу.")
    except Exception as e:
        print(f"[ERROR] Ошибка отправки уведомления админу: {e}")


# ===================== КОМАНДЫ =====================
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    """Обработчик команды /start с поддержкой метки источника"""
    user = message.from_user
    print(f"[MSG] {user.id} (@{user.username}): {message.text}")

    args = message.text.split()
    source = args[1] if len(args) > 1 else "DIRECT"

    save_or_update_lead(user.id, user.username, user.first_name, source)

    safe_name = html.escape(user.first_name or "Друг")
    text = (
        f"👋 <b>Привет, {safe_name}!</b>\n\n"
        f"🤖 Добро пожаловать в презентацию <b>Telegram-бота для Автодилеров и Автоподборщиков</b>!\n\n"
        f"Этот бот — мощный инструмент автоматизации продаж авто:\n"
        f"• 🎯 Автоматически собирает базу клиентов из Instagram, Telegram, Avito\n"
        f"• 🧮 Считает стоимость привоза и растаможки авто в 1 клик\n"
        f"• 📲 Отправляет вам мгновенные уведомления о новых заявках в Telegram\n"
        f"• 📊 Формирует выгружаемую базу клиентов в Excel/SQLite\n\n"
        f"👇 <b>Выберите раздел ниже для тестирования и просмотра тарифов:</b>"
    )

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=get_main_showcase_keyboard())


@bot.message_handler(commands=['db'])
def send_db(message: types.Message):
    """Выгрузка файла базы данных лидов администратору"""
    if message.from_user.id == YOUR_CHAT_ID:
        try:
            with open(DB_NAME, 'rb') as db_file:
                bot.send_document(
                    message.chat.id,
                    db_file,
                    caption=f"📂 Вот актуальная база лидов {os.path.basename(DB_NAME)}"
                )
                print("[ADMIN] Файл базы лидов отправлен админу.")
        except FileNotFoundError:
            bot.send_message(message.chat.id, "❌ База лидов ещё не создана.")
        except Exception as e:
            print(f"[ERROR] Ошибка отправки базы: {e}")
            bot.send_message(message.chat.id, f"❌ Ошибка отправки базы: {e}")
    else:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён.")


# ===================== CALLBACK-ОБРАБОТЧИКИ =====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    try:
        if data == "main_menu":
            text = (
                f"🏠 <b>Главное меню презентации AutoDealer Bot</b>\n\n"
                f"Выберите интересующий вас раздел:"
            )
            bot.edit_message_text(
                text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=get_main_showcase_keyboard()
            )

        elif data == "demo_menu":
            text = (
                f"🎮 <b>ИНТЕРАКТИВНЫЙ ТЕСТ-ДРАЙВ (Глазами вашего клиента)</b>\n\n"
                f"Попробуйте нажать на кнопки ниже. Именно так ваши клиенты будут взаимодействовать с ботом "
                f"при приходе из соцсетей или рекламы:"
            )
            bot.edit_message_text(
                text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=get_demo_keyboard()
            )

        elif data == "demo_catalog":
            card_text = (
                f"🚘 <b>ДЕМО-КАРТОЧКА: BMW X5 xDrive30d (2023)</b>\n\n"
                f"💰 <b>Цена под ключ:</b> 8 900 000 ₽\n"
                f"📍 <b>Статус:</b> Готов к отправке из Кореи\n"
                f"⚙️ <b>Двигатель:</b> 3.0 Дизель (286 л.с.) | Пробег: 18 000 км\n\n"
                f"💡 <i>В вашем готовом боте здесь будет ваш актуальный каталог авто с фото, ценами и описанием!</i>"
            )
            bot.edit_message_text(
                card_text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=get_demo_keyboard()
            )

        elif data == "demo_calc":
            calc_text = (
                f"🧮 <b>ДЕМО-КАЛЬКУЛЯТОР ПРИВОЗА</b>\n\n"
                f"🔹 <b>Марка:</b> Hyundai Palisade 2022 (2.2 Дизель)\n"
                f"🇰🇷 <b>Цена в Корее:</b> $32 000\n"
                f"🚢 <b>Логистика + Таможня:</b> ~1 450 000 ₽\n"
                f"✅ <b>Итого под ключ в РФ:</b> 4 650 000 ₽\n\n"
                f"💡 <i>Авто-расчёт экономит время менеджера и повышает конверсию заявок в 3 раза!</i>"
            )
            bot.edit_message_text(
                calc_text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=get_demo_keyboard()
            )

        elif data == "demo_auto_order":
            demo_alert_text = (
                f"🔔 <b>ДЕМО-УВЕДОМЛЕНИЕ ДИЛЕРУ:</b>\n\n"
                f"<i>«Новый клиент пришёл из Instagram и оставил заявку на BMW X5! Контакт записан в БД.»</i>\n\n"
                f"✅ <b>Именно так вам в Telegram будут мгновенно приходить горячие заявки с контактами клиентов!</b>"
            )
            bot.edit_message_text(
                demo_alert_text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=get_demo_keyboard()
            )

        elif data == "features_menu":
            features_text = (
                f"✨ <b>ВОЗМОЖНОСТИ СИСТЕМЫ AUTODEALER BOT:</b>\n\n"
                f"1️⃣ <b>Отслеживание источника трафика (Deep-linking)</b>\n"
                f"   Бот видит, откуда пришёл клиент: Instagram, Avito, Telegram-канал или реклама.\n\n"
                f"2️⃣ <b>Сбор и хранение базы клиентов (SQLite / Excel)</b>\n"
                f"   Ни один клиент не потеряется. Выгрузка базы в один клик через команду `/db`.\n\n"
                f"3️⃣ <b>Мгновенные уведомления владельцу</b>\n"
                f"   Как только человек запускает бота или оставляет заявку — вы получаете сообщение в Telegram.\n\n"
                f"4️⃣ <b>Калькулятор таможни и привоза авто</b>\n"
                f"   Автоматический расчёт расходов под ключ (Корея, Китай, ОАЭ).\n\n"
                f"5️⃣ <b>Работа 24/7 без сбоев и бана</b>\n"
                f"   Надёжная архитектура с шифрованием данных и логированием ошибок."
            )
            bot.edit_message_text(
                features_text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=get_back_keyboard()
            )

        elif data == "tariffs_menu":
            tariffs_text = (
                f"💎 <b>ТАРИФНЫЕ ПЛАНЫ НА БОТА:</b>\n\n"
                f"📦 <b>Тариф «Старт» — 15 000 ₽</b>\n"
                f"• Готовый бот под ваш бренд\n"
                f"• База клиентов + уведомления админу\n"
                f"• Настройка Deep-linking под Instagram/Avito\n\n"
                f"🚀 <b>Тариф «Профи» — 25 000 ₽</b>\n"
                f"• Всё из тарифа «Старт»\n"
                f"• Интерактивный Калькулятор доставки/таможни\n"
                f"• Каталог автомобилей с категориями\n\n"
                f"👑 <b>Тариф «VIP / Исходный код» — 45 000 ₽</b>\n"
                f"• Передача полного исходного кода Python\n"
                f"• Установка и деплой на ваш сервер\n"
                f"• Индивидуальные доработки под ваши задачи\n\n"
                f"👇 <b>Выберите тариф для оформления заявки:</b>"
            )
            bot.edit_message_text(
                tariffs_text, chat_id, call.message.message_id,
                parse_mode='HTML', reply_markup=get_tariffs_keyboard()
            )

        elif data.startswith("select_tariff_"):
            tariff_map = {
                "select_tariff_start": "Тариф «Старт» (15 000 ₽)",
                "select_tariff_pro": "Тариф «Профи» (25 000 ₽)",
                "select_tariff_vip": "Тариф «VIP / Исходный код» (45 000 ₽)"
            }
            selected_tariff = tariff_map.get(data, "Общий заказ")
            user_selected_tariffs[user_id] = selected_tariff

            prompt_text = (
                f"✅ Вы выбрали: <b>{selected_tariff}</b>\n\n"
                f"📱 Пожалуйста, нажмите кнопку <b>«Отправить номер телефона»</b> ниже "
                f"или напишите ваш контактный номер в чат, чтобы мы связались с вами для обсуждения деталей:"
            )
            bot.send_message(chat_id, prompt_text, parse_mode='HTML', reply_markup=get_contact_reply_keyboard())
            bot.answer_callback_query(call.id)

        elif data == "request_order":
            user_selected_tariffs[user_id] = "Запрос консультации"
            prompt_text = (
                f"📞 <b>Заявка на бесплатную консультацию по боту</b>\n\n"
                f"Нажмите кнопку <b>«Отправить номер телефона»</b> ниже или напишите ваш номер в чат:"
            )
            bot.send_message(chat_id, prompt_text, parse_mode='HTML', reply_markup=get_contact_reply_keyboard())
            bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"[ERROR] Callback handler error: {e}")


# ===================== ОБРАБОТКА КОНТАКТОВ И ТЕКСТА =====================
@bot.message_handler(content_types=['contact'])
def handle_contact(message: types.Message):
    """Обработчик отправки контакта через кнопку"""
    user = message.from_user
    phone = message.contact.phone_number
    interest = user_selected_tariffs.get(user.id, "Общий интерес")

    update_lead_contact(user.id, phone, interest)
    notify_admin_about_lead(user, phone, interest)

    thanks_text = (
        f"🎉 <b>Спасибо за заявку, {html.escape(user.first_name or '')}!</b>\n\n"
        f"Ваш номер <code>{html.escape(phone)}</code> успешно получен. "
        f"Мы свяжемся с вами в самое ближайшее время для обсуждения деталей бота!"
    )
    bot.send_message(
        message.chat.id, thanks_text, parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.send_message(
        message.chat.id, "👇 Вы можете продолжить изучение возможностей бота:",
        reply_markup=get_main_showcase_keyboard()
    )


@bot.message_handler(func=lambda msg: not msg.text.startswith('/'))
def handle_text(message: types.Message):
    """Обработчик текстовых сообщений (в т.ч. вручную введённых телефонов или отмены)"""
    text = message.text.strip()
    user = message.from_user

    if text == "❌ Отмена":
        bot.send_message(
            message.chat.id, "Действие отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.send_message(
            message.chat.id, "👇 Главное меню:",
            reply_markup=get_main_showcase_keyboard()
        )
        return

    cleaned_phone = "".join([c for c in text if c.isdigit() or c == '+'])
    if len(cleaned_phone) >= 7:
        interest = user_selected_tariffs.get(user.id, "Введён вручную")
        update_lead_contact(user.id, cleaned_phone, interest)
        notify_admin_about_lead(user, cleaned_phone, interest)

        thanks_text = (
            f"🎉 <b>Спасибо! Заявка принята.</b>\n\n"
            f"Номер <code>{html.escape(cleaned_phone)}</code> зарегистрирован. "
            f"Скоро свяжемся с вами!"
        )
        bot.send_message(
            message.chat.id, thanks_text, parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.send_message(
            message.chat.id, "👇 Вы можете продолжить просмотр:",
            reply_markup=get_main_showcase_keyboard()
        )
    else:
        default_reply = (
            f"💡 Используйте меню ниже для тестирования бота или отправьте ваш телефон для связи:"
        )
        bot.send_message(message.chat.id, default_reply, reply_markup=get_main_showcase_keyboard())


# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    init_db()
    print(f"[INFO] Бот-Продавец Showcase запущен. База данных: {DB_NAME}")
    bot.infinity_polling(skip_pending=True)
