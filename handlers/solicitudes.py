# handlers/solicitudes.py
from bot_instance import bot
from config import logger, CATEGORIES
import telebot

@bot.message_handler(commands=['nueva_solicitud'])
def nueva_solicitud_command(message):
    chat_id = message.chat.id
    
    # 2. Selección de categoría
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    
    category_list = []
    for num, name in CATEGORIES.items():
        category_list.append(f"{num}. {name}")
    
    # Organizar en dos columnas
    markup.row(category_list[0], category_list[1])
    markup.row(category_list[2], category_list[3])
    
    msg = "📦 **NUEVA SOLICITUD**\n\n"
    msg += "Paso 1: Selecciona la categoría de transporte que necesitas:"
    
    # Lógica: Aquí se debe cambiar el estado del usuario para esperar la selección de categoría
    
    bot.send_message(chat_id, msg, reply_markup=markup)
