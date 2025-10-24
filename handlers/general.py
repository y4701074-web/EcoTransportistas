# handlers/general.py
from bot_instance import bot
from config import logger, STATE_ACTIVE

@bot.message_handler(commands=['menu', 'help'])
def send_menu(message):
    msg = "🛠️ **Menú Principal**\n\n"
    msg += "Funciones Comunes:\n"
    msg += "  - /nueva_solicitud: Iniciar un nuevo pedido de transporte.\n"
    msg += "  - /perfil: Ver o modificar tu configuración.\n\n"
    msg += "Si eres Administrador, usa /admin_panel."
    bot.send_message(message.chat.id, msg)
