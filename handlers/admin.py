# handlers/admin.py
from bot_instance import bot
from config import logger, ADMIN_SUPREMO_ID, ADMIN_SUPREMO_USERNAME
from db import get_db_connection

# --- Funciones de Utilidad ---
def is_supremo(chat_id):
    """Verifica si el chat_id corresponde al Administrador Supremo."""
    return chat_id == ADMIN_SUPREMO_ID

def get_admin_level(chat_id):
    """Obtiene el nivel de administración (0=No Admin, 9=Supremo)."""
    conn = get_db_connection()
    user = conn.execute("SELECT es_admin FROM usuarios WHERE chat_id = ?", (chat_id,)).fetchone()
    conn.close()
    return user['es_admin'] if user else 0

# --- Comandos del Admin Supremo ---
@bot.message_handler(commands=['admin_panel_supremo', 'admin_crear_pais', 'admin_crear_provincia', 'admin_crear_zona', 'admin_designar_supremo'])
def admin_supremo_commands(message):
    chat_id = message.chat.id
    command = message.text.split()[0]
    
    if get_admin_level(chat_id) != 9:
        bot.send_message(chat_id, "Acceso denegado. Este comando es exclusivo del Admin Supremo.")
        return
    
    if command == '/admin_panel_supremo':
        msg = f"👑 **PANEL SUPREMO - {ADMIN_SUPREMO_USERNAME}**\n\n"
        msg += "COMANDOS EXCLUSIVOS:\n"
        msg += "  - /admin_crear_pais [nombre_pais] [admin_id]\n"
        msg += "  - /admin_crear_provincia [pais_id] [nombre_provincia] [admin_id]\n"
        msg += "  - /admin_crear_zona [provincia_id] [nombre_zona] [admin_id]\n"
        msg += "  - /admin_designar_supremo [nuevo_admin_id]\n\n"
        msg += "¡Control total sobre la jerarquía territorial y de administración!"
        bot.send_message(chat_id, msg)
    else:
        bot.send_message(chat_id, f"Comando '{command}' recibido. Implementación de lógica de creación en curso...")

# --- Panel General de Administración ---
@bot.message_handler(commands=['admin_panel'])
def admin_panel_general(message):
    chat_id = message.chat.id
    admin_level = get_admin_level(chat_id)
    
    if admin_level > 0:
        bot.send_message(chat_id, f"Bienvenido al Panel de Administración (Nivel {admin_level}).")
    else:
        bot.send_message(chat_id, "No tienes permisos de administración.")
