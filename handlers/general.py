import sqlite3
from bot_instance import bot, user_states
from db import get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger
import keyboards

# ESTA ES LA FUNCIÓN QUE TENÍA EL ERROR DE INDENTACIÓN
def show_main_menu(chat_id, user_id):
    """Mostrar menú principal según tipo de usuario"""
    try:
        user_db = get_user_by_telegram_id(user_id)
        if not user_db:
            logger.warning(f"No se encontró usuario {user_id} para mostrar menú")
            return

        user_type = user_db['tipo']
        markup = keyboards.get_main_menu_keyboard(user_type)
        
        bot.send_message(chat_id, get_message('main_menu', user_id), 
                        reply_markup=markup, parse_mode='Markdown')
                        
    except Exception as e:
        logger.error(f"Error mostrando menú principal: {e}")
        

# MANEJO DE MENSAJES DE TEXTO
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not message.text:
        return
        
    if message.text.startswith('/'):
        # Permitir que los comandos se procesen
        return
    
    user = message.from_user
    
    # Si está en un estado (ej. 'request_description'), los handlers específicos
    # de ese estado (definidos en handlers/solicitudes.py) se ejecutarán primero.
    
    # Si no está en un estado FSM, mostrar menú principal
    if user.id not in user_states:
        show_main_menu(message.chat.id, user.id)
    else:
        # Si está en un estado pero el mensaje no coincide con ningún
        # handler de estado, recordarle que complete el proceso.
        bot.reply_to(message, "⚠️ Completa el proceso actual primero")
      
