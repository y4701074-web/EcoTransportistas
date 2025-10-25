# handlers/solicitante.py
from bot_instance import bot
from config import logger
from db import get_user_by_telegram_id

# Implementación de la acción para el botón "Ver Solicitudes"
def ver_solicitudes_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        bot.send_message(chat_id, "❌ Primero completa tu registro con /start")
        return
    
    msg = "📦 **Mis Solicitudes**\n\n"
    msg += "**Funcionalidades:**\n"
    msg += "• Ver solicitudes activas\n"
    msg += "• Historial de solicitudes\n"
    msg += "• Estado de envíos\n\n"
    msg += "📋 *Ejemplo:*\n"
    msg += "• Solicitud #123 - En proceso\n"
    msg += "• Solicitud #124 - Completada\n"
    msg += "• Solicitud #125 - Cancelada\n\n"
    msg += "Usa /nueva_solicitud para crear una nueva."
    
    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['perfil_solicitante'])
def perfil_solicitante_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    if not user_data:
        bot.send_message(chat_id, "❌ Primero completa tu registro con /start")
        return
    
    from geography_db import get_geographic_level_name
    
    # Obtener nombres geográficos
    pais_nombre = get_geographic_level_name('pais', user_data.get('pais_id'))
    provincia_nombre = get_geographic_level_name('provincia', user_data.get('provincia_id'))
    zona_nombre = get_geographic_level_name('zona', user_data.get('zona_id'))
    
    msg = "👤 **Mi Perfil**\n\n"
    msg += f"**Nombre:** {user_data['nombre_completo']}\n"
    msg += f"**Teléfono:** {user_data['telefono'] or 'No registrado'}\n"
    msg += f"**Rol:** {user_data['tipo'].title()}\n"
    msg += f"**Ubicación:** {pais_nombre} / {provincia_nombre} / {zona_nombre}\n"
    msg += f"**Estado:** {user_data['estado'].title()}\n\n"
    msg += "✏️ *Usa /menu para más opciones*"
    
    bot.send_message(chat_id, msg)