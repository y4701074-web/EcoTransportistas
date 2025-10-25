# handlers/solicitudes.py
from bot_instance import bot
from config import logger, CATEGORIES
from db import get_user_by_telegram_id
import telebot

@bot.message_handler(commands=['nueva_solicitud'])
def nueva_solicitud_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        bot.send_message(chat_id, "❌ Primero completa tu registro con /start")
        return
    
    # Verificar que sea solicitante
    if user_data['tipo'] not in ['solicitante', 'ambos']:
        bot.send_message(chat_id, "❌ Esta función es solo para solicitantes")
        return
    
    msg = "📦 **NUEVA SOLICITUD**\n\n"
    msg += "Vamos a crear una nueva solicitud de transporte.\n\n"
    msg += "**Paso 1: Tipo de Vehículo**\n"
    msg += "Selecciona el tipo de vehículo que necesitas:"
    
    # Usar teclado de tipos de vehículo
    from keyboards import get_vehicle_type_keyboard
    markup = get_vehicle_type_keyboard()
    
    bot.send_message(chat_id, msg, reply_markup=markup)

# Handler para selección de tipo de vehículo
@bot.callback_query_handler(func=lambda call: call.data.startswith('vehicle_'))
def handle_vehicle_selection(call):
    user = call.from_user
    chat_id = call.message.chat.id
    
    vehicle_type = call.data.split('_')[1]
    
    msg = "🚚 **Tipo de Vehículo Seleccionado**\n\n"
    msg += f"Vehículo: {vehicle_type.title()}\n\n"
    msg += "**Paso 2: Tipo de Carga**\n"
    msg += "Selecciona el tipo de carga:"
    
    from keyboards import get_cargo_type_keyboard
    markup = get_cargo_type_keyboard()
    
    bot.edit_message_text(
        msg,
        chat_id,
        call.message.message_id,
        reply_markup=markup
    )

# Handler para selección de tipo de carga
@bot.callback_query_handler(func=lambda call: call.data.startswith('cargo_'))
def handle_cargo_selection(call):
    user = call.from_user
    chat_id = call.message.chat.id
    
    cargo_type = call.data.split('_')[1]
    
    msg = "📦 **Tipo de Carga Seleccionado**\n\n"
    msg += f"Carga: {cargo_type.replace('_', ' ').title()}\n\n"
    msg += "**Paso 3: Descripción**\n"
    msg += "Por favor, describe brevemente lo que necesitas transportar:\n"
    msg += "(Ej: '2 cajas de ropa', '1 mueble de 2 metros', etc.)"
    
    # Aquí deberías guardar el estado FSM para esperar la descripción
    # Por ahora solo mostramos el mensaje
    bot.edit_message_text(
        msg,
        chat_id,
        call.message.message_id
    )
    
    # En un flujo completo, aquí cambiarías el estado del usuario para esperar la descripción