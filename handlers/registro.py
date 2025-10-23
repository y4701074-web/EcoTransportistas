import sqlite3
from telebot.types import ReplyKeyboardRemove
from bot_instance import bot, user_states
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger, PROVINCIAS_CUBA, ZONAS_POR_PROVINCIA
import keyboards
# ELIMINAR ESTA LÍNEA: from .general import show_main_menu 

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user = message.from_user
        user_id = user.id
        
        existing_user = get_user_by_telegram_id(user_id)
            
        if existing_user:
            # SOLUCIÓN DE IMPORTACIÓN CIRCULAR 2: IMPORTACIÓN LOCAL
            from .general import show_main_menu 
            
            welcome_text = get_message('welcome', user_id, name=user.first_name)
            bot.reply_to(message, welcome_text, parse_mode='Markdown')
            show_main_menu(message.chat.id, user_id) # Mostrar menú si ya existe
            return
        
        # ... (resto del código)
        
# ... (otras funciones intermedias)

@bot.callback_query_handler(func=lambda call: call.data.startswith('zona_'))
def handle_zona_selection(call):
    try:
        # ... (lógica de registro y guardado en DB)
        
        # ... (mostrar mensaje de confirmación)
        
        # SOLUCIÓN DE IMPORTACIÓN CIRCULAR 2: IMPORTACIÓN LOCAL
        from .general import show_main_menu 
        
        # Mostrar menú de acciones
        show_main_menu(call.message.chat.id, user.id)
        
        # ... (limpiar estado)
        
    except Exception as e:
        logger.error(f"Error en handle_zona_selection: {e}")

