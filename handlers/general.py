# handlers/general.py
from bot_instance import bot
from config import logger, STATE_ACTIVE, STATE_WAITING_ROLE, ROLE_SOLICITANTE, ROLE_TRANSPORTISTA, ROLE_AMBOS
from db import get_db_connection
import telebot

# --- Funciones de Utilidad ---
def get_user_data(chat_id):
    conn = get_db_connection()
    user = conn.execute("SELECT estado, rol FROM usuarios WHERE chat_id = ?", (chat_id,)).fetchone()
    conn.close()
    return user if user else None

def create_main_menu_keyboard(rol):
    """Crea el teclado del menú principal basado en el rol del usuario."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Opciones comunes
    markup.add("👤 Mi Perfil")
    
    # Opciones para Solicitante (SOLICITANTE o AMBOS)
    if ROLE_SOLICITANTE in rol or ROLE_AMBOS in rol:
        markup.add("📦 Ver Solicitudes")
    
    # Opciones para Transportista (TRANSPORTISTA o AMBOS)
    if ROLE_TRANSPORTISTA in rol or ROLE_AMBOS in rol:
        markup.add("🚚 Mis Vehículos", "📍 Mis Zonas") 
        
    return markup

def handle_role_prompt(message):
    """Genera y envía el prompt para la elección de rol."""
    chat_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row("📦 Solo Solicitante")
    markup.row("🚚 Solo Transportista")
    markup.row("🔄 Ambos (Solicitante + Transportista)")
    
    bot.send_message(chat_id, "Paso de Registro: ¿Cuál será tu rol principal en el sistema?", reply_markup=markup)


# --- Comandos y Handlers del Menú ---
@bot.message_handler(commands=['menu', 'help'])
def send_menu(message):
    chat_id = message.chat.id
    user_data = get_user_data(chat_id)

    if user_data and user_data['estado'] == STATE_ACTIVE:
        rol = user_data['rol']
        markup = create_main_menu_keyboard(rol)
        msg = "🛠️ **Menú Principal** - Elige una opción según tu rol."
        bot.send_message(chat_id, msg, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Por favor, usa /start para iniciar o continuar tu registro.")

# CRÍTICO: Manejo de Botones del Menú Principal (filtros de texto)
@bot.message_handler(func=lambda message: message.text in ["👤 Mi Perfil", "📦 Ver Solicitudes", "🚚 Mis Vehículos", "📍 Mis Zonas"])
def handle_menu_buttons(message):
    chat_id = message.chat.id
    text = message.text
    
    # Se usan importaciones locales para evitar dependencias circulares
    if text == "👤 Mi Perfil":
        bot.send_message(chat_id, "Abriendo tu perfil... (Aquí se podrá cambiar nombre, teléfono, etc.).")
    elif text == "📦 Ver Solicitudes":
        from handlers.solicitante import ver_solicitudes_command
        ver_solicitudes_command(message)
    elif text == "🚚 Mis Vehículos":
        from handlers.transportista import mis_vehiculos_command
        mis_vehiculos_command(message)
    elif text == "📍 Mis Zonas":
        from handlers.transportista import mis_zonas_command
        mis_zonas_command(message)
    else:
        bot.send_message(chat_id, "Acción no reconocida. Usa /menu.")

# Fallback para mensajes que no son comandos ni botones (si no están en un flujo)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    user_data = get_user_data(message.chat.id)
    if user_data and user_data['estado'] == STATE_ACTIVE:
         bot.send_message(message.chat.id, "Mensaje genérico. Usa /menu para ver las opciones principales.")
    # Si el usuario está en un estado de registro, el handler específico lo captura.
    pass
