# handlers/general.py
from bot_instance import bot
from config import logger, STATE_ACTIVE, ROLE_SOLICITANTE, ROLE_TRANSPORTISTA, ROLE_AMBOS
from db import get_user_by_telegram_id
import telebot
import keyboards

# --- Funciones de Utilidad ---
def get_user_data(telegram_id):
    user = get_user_by_telegram_id(telegram_id)
    return user if user else None

def create_main_menu_keyboard(user_type, is_admin=False):
    """Crea el teclado del menú principal basado en el rol del usuario."""
    return keyboards.get_main_menu_keyboard(user_type, is_admin)

# --- Comandos y Handlers del Menú ---
@bot.message_handler(commands=['menu', 'help'])
def send_menu(message):
    user = message.from_user
    chat_id = message.chat.id
    user_data = get_user_data(user.id)

    if user_data and user_data['estado'] == STATE_ACTIVE:
        rol = user_data['tipo']
        
        # Verificar si es admin
        from db import get_admin_data
        is_admin = get_admin_data(user.id) is not None
        
        markup = create_main_menu_keyboard(rol, is_admin)
        msg = "🛠️ **Menú Principal** - Elige una opción según tu rol."
        bot.send_message(chat_id, msg, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Por favor, usa /start para iniciar o continuar tu registro.")

# CRÍTICO: Manejo de Botones del Menú Principal
@bot.message_handler(func=lambda message: message.text in [
    "👤 Mi Perfil", "🚗 Mis Vehículos", "📦 Nueva Solicitud", 
    "🔎 Ver Solicitudes", "🗺️ Mis Zonas (Filtros)", "👑 Panel Admin"
])
def handle_menu_buttons(message):
    user = message.from_user
    chat_id = message.chat.id
    text = message.text
    
    user_data = get_user_data(user.id)
    if not user_data or user_data['estado'] != STATE_ACTIVE:
        bot.send_message(chat_id, "❌ Primero completa tu registro con /start")
        return
    
    if text == "👤 Mi Perfil":
        from handlers.solicitante import perfil_solicitante_command
        perfil_solicitante_command(message)
        
    elif text == "🚗 Mis Vehículos":
        from handlers.transportista import mis_vehiculos_command
        mis_vehiculos_command(message)
        
    elif text == "📦 Nueva Solicitud":
        from handlers.solicitudes import nueva_solicitud_command
        nueva_solicitud_command(message)
        
    elif text == "🔎 Ver Solicitudes":
        from handlers.transportista import ver_solicitudes_command
        ver_solicitudes_command(message)
        
    elif text == "🗺️ Mis Zonas (Filtros)":
        from handlers.transportista import mis_zonas_command
        mis_zonas_command(message)
        
    elif text == "👑 Panel Admin":
        from handlers.admin import admin_panel
        admin_panel(message)
        
    else:
        bot.send_message(chat_id, "Acción no reconocida. Usa /menu.")

# Fallback para mensajes no reconocidos
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    user_data = get_user_data(message.from_user.id)
    if user_data and user_data['estado'] == STATE_ACTIVE:
        bot.send_message(message.chat.id, "ℹ️ Usa /menu para ver las opciones principales.")