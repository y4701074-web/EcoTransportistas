import sqlite3
from bot_instance import bot, user_states
from db import get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger
import keyboards
# ELIMINAR ESTA LÍNEA: from .registro import send_welcome 


# ... (Función show_main_menu sin cambios)


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
            
            # --- SOLUCIÓN AL ERROR CIRCULAR ---
            # Importamos la función aquí, justo antes de usarla,
            # para que el módulo general.py pueda cargarse completamente
            # antes de intentar cargar registro.py.
            from .registro import send_welcome 
            
            send_welcome(message) 
            
    else:
        # Si está en un estado pero el mensaje no coincide con ningún
        # handler de estado, recordarle que complete el proceso.
        bot.reply_to(message, "⚠️ Completa el proceso actual primero")
