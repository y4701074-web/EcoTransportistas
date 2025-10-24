# handlers/solicitante.py
from bot_instance import bot
from config import logger

# Implementación de la acción para el botón "Ver Solicitudes"
def ver_solicitudes_command(message):
    chat_id = message.chat.id
    
    msg = "📦 **Mis Solicitudes**\n\n"
    msg += "Funcionalidad: Listado de solicitudes activas y cerradas.\n"
    msg += "Ejemplo: Tienes 1 solicitud activa (ID: 123) y 5 solicitudes cerradas.\n"
    msg += "Usa /nueva_solicitud para crear una nueva."
    
    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['perfil_solicitante'])
def perfil_solicitante_command(message):
    # Lógica específica para ver el perfil o historial de solicitudes.
    bot.send_message(message.chat.id, "Mostrando perfil de Solicitante.")
