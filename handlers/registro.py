import sqlite3
from telebot.types import ReplyKeyboardRemove
from bot_instance import bot, user_states
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger, PROVINCIAS_CUBA, ZONAS_POR_PROVINCIA
import keyboards
# ELIMINAR ESTA LÍNEA para romper la Importación Circular: from .general import show_main_menu

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
        
        # ... (resto de la función)
        
    except Exception as e:
        logger.error(f"Error en /start: {e}")
        bot.reply_to(message, "❌ Error iniciando el bot. Intenta nuevamente.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_language_selection(call):
    # ... (cuerpo de la función)
    # ... (Asegúrate de que termina con un except)

# ... (Otras funciones intermedias)

@bot.callback_query_handler(func=lambda call: call.data.startswith('prov_'))
def handle_provincia_selection(call):
    try:
        # ... (cuerpo de la función sin cambios)
        
        bot.edit_message_text(
            get_message('provincia_selected', user.id, provincia=provincia_name),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e: # ✅ Esta línea debe existir y estar correctamente indentada.
        logger.error(f"Error selección provincia: {e}") 

@bot.callback_query_handler(func=lambda call: call.data.startswith('zona_'))
def handle_zona_selection(call):
    try:
        user = call.from_user
        zona = call.data.split('_')[1]
        
        user_data = user_states[user.id]
        
        # Guardar usuario en base de datos
        # ... (código de guardado de DB)
        
        # Mensaje de confirmación
        # ... (código de mensaje de confirmación)
        
        # Importación local para romper el ciclo
        from .general import show_main_menu 
        
        # Mostrar menú de acciones
        show_main_menu(call.message.chat.id, user.id)
        
        # Limpiar estado
        if user.id in user_states:
