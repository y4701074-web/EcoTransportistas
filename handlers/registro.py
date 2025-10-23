import sqlite3
from telebot.types import ReplyKeyboardRemove
from bot_instance import bot, user_states
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger, PROVINCIAS_CUBA, ZONAS_POR_PROVINCIA
import keyboards
# ELIMINA ESTA LÍNEA para romper la Importación Circular: from .general import show_main_menu

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user = message.from_user
        user_id = user.id
        
        existing_user = get_user_by_telegram_id(user_id)
            
        if existing_user:
            # Importación local para romper el ciclo
            from .general import show_main_menu 
            
            welcome_text = get_message('welcome', user_id, name=user.first_name)
            bot.reply_to(message, welcome_text, parse_mode='Markdown')
            show_main_menu(message.chat.id, user_id) # Mostrar menú si ya existe
            return
        
        # Si no está registrado, pedir idioma
        markup = keyboards.get_language_keyboard()
        bot.reply_to(message, get_message('choose_language', user_id), 
                    reply_markup=markup, parse_mode='Markdown')
        
        log_audit("start_command", user_id)
        
    except Exception as e:
        logger.error(f"Error en /start: {e}")
        bot.reply_to(message, "❌ Error iniciando el bot. Intenta nuevamente.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_language_selection(call):
    try:
        # ... (Cuerpo de la función)
        # ...
    except Exception as e:
        logger.error(f"Error selección idioma: {e}")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    try:
        # ... (Cuerpo
