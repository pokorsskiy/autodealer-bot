"""
Шаблон нового хэндлера команд или текста для быстрых сниппетов.
"""

from telebot import types
import html

def register_example_handler(bot, YOUR_CHAT_ID):
    @bot.message_handler(commands=['help'])
    def help_command(message: types.Message):
        user = message.from_user
        safe_name = html.escape(user.first_name or "Гость")
        
        text = f"👋 Здравствуйте, <b>{safe_name}</b>!\n Чем я могу вам помочь?"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Поддержка", url="https://t.me/dealer_auto"))
        
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
