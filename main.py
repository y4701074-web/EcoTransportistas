import os
import logging
import sqlite3
from datetime import datetime
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Configuración logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8405097042:AAF-ytt1h5o-woafNakYGDHcoi1mh_S5pQ8')
ADMIN_SUPREMO = os.environ.get('ADMIN_SUPREMO', '@Y_0304')

# Inicializar bot
bot = telebot.TeleBot(BOT_TOKEN)

# Inicializar base de datos
def init_db():
    try:
        conn = sqlite3.connect('ecotransportistas.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                nombre_completo TEXT,
                telefono TEXT,
                tipo TEXT,
                pais TEXT DEFAULT 'Cuba',
                provincia TEXT,
                zona TEXT,
                estado TEXT DEFAULT 'activo',
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
        return False

# Comandos del bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user = message.from_user
        welcome_text = f"""
🚀 <b>¡Bienvenido a EcoTransportistas!</b>

👋 Hola {user.first_name}

🌍 <i>Conectando transportistas y solicitantes en Cuba</i>

📝 Usa /registro para comenzar
🆘 Usa /ayuda para ver todos los comandos
        """
        bot.reply_to(message, welcome_text, parse_mode='HTML')
        logger.info(f"Usuario {user.id} usó /start")
    except Exception as e:
        logger.error(f"Error en /start: {e}")

@bot.message_handler(commands=['ayuda'])
def send_help(message):
    help_text = """
🆘 <b>COMANDOS DISPONIBLES</b>

👤 <b>Para Usuarios:</b>
/start - Iniciar el bot
/ayuda - Mostrar esta ayuda
/registro - Registrarse en el sistema
/mis_datos - Ver mi información

👑 <b>Para Administradores:</b>
/admin_panel - Panel de control administrativo

🚀 <b>Próximamente:</b>
/nueva_solicitud - Publicar nueva solicitud
/ver_solicitudes - Ver solicitudes disponibles
/mis_zonas - Configurar zonas de trabajo
"""
    bot.reply_to(message, help_text, parse_mode='HTML')

@bot.message_handler(commands=['registro'])
def start_registration(message):
    bot.reply_to(message, 
        "📝 <b>Registro de Usuario</b>\n\n"
        "🔜 <i>Esta funcionalidad estará disponible muy pronto</i>\n\n"
        "Mientras tanto, puedes:\n"
        "• Explorar los comandos con /ayuda\n" 
        "• Contactar al administrador: @Y_0304",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['mis_datos'])
def show_my_data(message):
    user = message.from_user
    user_info = f"""
👤 <b>Tu Información</b>

🆔 ID: <code>{user.id}</code>
👤 Username: @{user.username if user.username else 'No tiene'}
📛 Nombre: {user.first_name} {user.last_name or ''}

🔜 <i>Registro completo disponible próximamente</i>
"""
    bot.reply_to(message, user_info, parse_mode='HTML')

@bot.message_handler(commands=['admin_panel'])
def admin_panel(message):
    user = message.from_user
    if user.username != ADMIN_SUPREMO.replace('@', ''):
        bot.reply_to(message,
            "❌ <b>Acceso Denegado</b>\n\n"
            "Solo el administrador supremo puede acceder a este panel.",
            parse_mode='HTML'
        )
        return
    
    admin_text = f"""
👑 <b>Panel de Administración Suprema</b>

👋 Bienvenido, {user.first_name}

📊 <b>Estado del Sistema:</b>
✅ Bot: Operativo con pyTelegramBotAPI
🗄️ Base de datos: Inicializada
🌐 Plataforma: PythonAnywhere 24/7
👥 Usuarios registrados: Próximamente

🔧 <b>Acciones disponibles:</b>
• Configurar estructura administrativa
• Gestionar usuarios  
• Ver estadísticas

🔜 <i>Panel completo en desarrollo</i>
"""
    bot.reply_to(message, admin_text, parse_mode='HTML')

# Manejar mensajes de texto normales
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        return
    
    bot.reply_to(message,
        f"🤖 <b>EcoTransportistas Bot</b>\n\n"
        f"Recibí tu mensaje: <code>{message.text}</code>\n\n"
        f"Usa /ayuda para ver los comandos disponibles.",
        parse_mode='HTML'
    )

# Función principal
def main():
    logger.info("🚀 Iniciando EcoTransportistas Bot con pyTelegramBotAPI...")
    
    # Inicializar base de datos
    if init_db():
        logger.info("✅ Base de datos lista")
    else:
        logger.error("❌ Error crítico con base de datos")
        return
    
    # Iniciar el bot
    try:
        logger.info("🤖 Bot iniciado - Escuchando mensajes...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"❌ Error en el bot: {e}")

if __name__ == '__main__':
    main()
