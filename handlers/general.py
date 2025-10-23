import sqlite3
from bot_instance import bot, user_states
from db import get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger
import keyboards
# ELIMINAR LA IMPORTACIÓN AQUÍ: from .registro import send_welcome 


def show_main_menu(chat_id, user_id):
    # ... (cuerpo de la función sin cambios)
    # ...


# MANEJO DE MENSAJES DE TEXTO
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # ... (lógica de verificación de mensaje y comandos)
    
    user = message.from_user
    
    if user.id not in user_states:
        
        user_db = get_user_by_telegram_id(user.id)
        
        if user_db:
            show_main_menu(message.chat.id, user.id)
        else:
            # SOLUCIÓN DE IMPORTACIÓN CIRCULAR 1: IMPORTACIÓN LOCAL
            from .registro import send_welcome 
            
            send_welcome(message) 
            
    else:
        bot.reply_to(message, "⚠️ Completa el proceso actual primero")
