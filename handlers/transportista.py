# handlers/transportista.py
from bot_instance import bot
from config import logger
from db import get_user_by_telegram_id
import keyboards

# Implementación de la acción para el botón "Mis Vehículos"
def mis_vehiculos_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        bot.send_message(chat_id, "❌ Primero completa tu registro con /start")
        return
    
    msg = "🚚 **Mis Vehículos**\n\n"
    msg += "Aquí podrás gestionar los vehículos asociados a tu cuenta.\n\n"
    msg += "🚗 **Funciones disponibles:**\n"
    msg += "• Añadir nuevo vehículo\n"
    msg += "• Ver vehículos registrados\n"
    msg += "• Eliminar vehículos\n"
    msg += "• Configurar capacidad de carga\n\n"
    msg += "🔧 *Próximamente disponible...*"
    
    bot.send_message(chat_id, msg)

# Implementación de la acción para el botón "Mis Zonas"
def mis_zonas_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        bot.send_message(chat_id, "❌ Primero completa tu registro con /start")
        return
    
    # Verificar que sea transportista
    if user_data['tipo'] not in [ROLE_TRANSPORTISTA, ROLE_AMBOS]:
        bot.send_message(chat_id, "❌ Esta función es solo para transportistas")
        return
    
    msg = "📍 **Mis Zonas de Trabajo**\n\n"
    msg += "Configura las zonas donde quieres recibir solicitudes de transporte.\n\n"
    
    markup = keyboards.get_work_zones_menu(user.id)
    if markup:
        bot.send_message(chat_id, msg, reply_markup=markup)
    else:
        bot.send_message(chat_id, "❌ Error al cargar el menú de zonas")

# Nueva función para el botón "Ver Solicitudes"
def ver_solicitudes_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        bot.send_message(chat_id, "❌ Primero completa tu registro con /start")
        return
    
    # Verificar que sea transportista
    if user_data['tipo'] not in [ROLE_TRANSPORTISTA, ROLE_AMBOS]:
        bot.send_message(chat_id, "❌ Esta función es solo para transportistas")
        return
    
    msg = "🔎 **Solicitudes Disponibles**\n\n"
    msg += "Buscando solicitudes en tus zonas de trabajo...\n\n"
    
    from db import get_requests_for_transportista
    solicitudes = get_requests_for_transportista(user_data)
    
    if solicitudes:
        msg += f"📦 **Encontradas {len(solicitudes)} solicitudes:**\n\n"
        for i, solicitud in enumerate(solicitudes[:5], 1):  # Mostrar máximo 5
            msg += f"{i}. #{solicitud['id']} - {solicitud['cargo_type']}\n"
        if len(solicitudes) > 5:
            msg += f"\n... y {len(solicitudes) - 5} más"
    else:
        msg += "😔 No hay solicitudes activas en tus zonas de trabajo."
    
    bot.send_message(chat_id, msg)

# Comandos de Configuración Post-Registro
@bot.message_handler(commands=['config_transportista'])
def config_transportista_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    if not user_data or user_data['tipo'] not in [ROLE_TRANSPORTISTA, ROLE_AMBOS]:
        bot.send_message(chat_id, "❌ Esta función es solo para transportistas")
        return
    
    bot.send_message(chat_id, "🚚 Iniciando configuración de Transportista...")
    mis_zonas_command(message)  # Empezar con la configuración de zonas