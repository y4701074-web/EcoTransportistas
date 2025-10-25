# handlers/solicitudes.py
from bot_instance import bot
from config import logger, CATEGORIES, ROLE_SOLICITANTE, ROLE_AMBOS, MESSAGES
import telebot
# Nota: get_user_by_telegram_id debe estar definido en db.py para que esto funcione
from db import get_user_by_telegram_id 

@bot.message_handler(commands=['nueva_solicitud'])
def nueva_solicitud_command(message):
    chat_id = message.chat.id
    user_data = get_user_by_telegram_id(chat_id)
    
    # 1. Pre-verificación de rol (Se asume idioma 'es')
    if not user_data or user_data.get('tipo') not in [ROLE_SOLICITANTE, ROLE_AMBOS]:
        msg_error = MESSAGES['es'].get('error_not_solicitante', "❌ Solo solicitantes pueden crear solicitudes.")
        bot.send_message(chat_id, msg_error, parse_mode="Markdown")
        return

    # 2. Selección del Tipo de Vehículo (Primera categoría)
    
    # 🚨 CORRECCIÓN CRÍTICA: Se debe acceder a la lista anidada 'VEHICLE_TYPES' y usarla directamente
    vehicle_types = CATEGORIES.get('VEHICLE_TYPES', []) 
    
    if not vehicle_types:
        bot.send_message(chat_id, "❌ Error de configuración: No se encontraron tipos de vehículo en CATEGORIES.")
        return
        
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    
    # Usamos el operador * para desempaquetar la lista y añadirla como botones
    # Esto reemplaza la lógica incorrecta del for loop y las llamadas a markup.row manuales.
    markup.add(*vehicle_types, row_width=2) 
    
    # Usamos el mensaje de config.py (asumiendo idioma 'es')
    msg = MESSAGES['es'].get('request_vehicle_type', "🚗 ¿Qué tipo de vehículo necesitas para el transporte?")
    
    # Lógica de FSM: Aquí se debe cambiar el estado del usuario para esperar la selección 
    # (Ej: set_user_state(chat_id, STATE_WAITING_VEHICLE_TYPE))
    
    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")
