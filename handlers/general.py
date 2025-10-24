import sqlite3
from bot_instance import bot, user_states
from db import get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger
import keyboards
# ELIMINADA LA IMPORTACIÓN CIRCULAR de la cabecera

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
    
    # Si no está en un estado FSM, determinar si está registrado o si debe registrarse
    if user.id not in user_states:
        
        # 1. Intentar buscar al usuario en la base de datos
        user_db = get_user_by_telegram_id(user.id)
        
        if user_db:
            # 2. Si está registrado, mostrar el menú principal
            show_main_menu(message.chat.id, user.id)
        else:
            # 3. Si NO está registrado, iniciar el proceso de bienvenida/registro
            
            # Importación local para romper el ciclo
            from .registro import send_welcome 
            
            send_welcome(message) # Se llama al handler /start
            
    else:
        # Si está en un estado pero el mensaje no coincide con ningún
        # handler de estado, recordarle que complete el proceso.
        bot.reply_to(message, "⚠️ Completa el proceso actual primero")
