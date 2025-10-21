import os
import logging
import sqlite3
from datetime import datetime
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests

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
        conn = sqlite3.connect('/app/ecotransportistas.db')
        cursor = conn.cursor()
        
        # Tabla de usuarios
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
        
        # Tabla de administradores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                nivel TEXT,
                region_asignada TEXT,
                comision_transportistas INTEGER DEFAULT 100,
                comision_solicitantes INTEGER DEFAULT 50,
                porcentaje_superior INTEGER DEFAULT 20,
                estado TEXT DEFAULT 'activo',
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabla de solicitudes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solicitudes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                tipo_carga TEXT,
                descripcion TEXT,
                direccion_desde TEXT,
                direccion_hacia TEXT,
                presupuesto INTEGER,
                estado TEXT DEFAULT 'activa',
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
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
👑 Admin: /admin_panel
        """
        bot.reply_to(message, welcome_text, parse_mode='HTML')
        logger.info(f"Usuario {user.id} usó /start")
        
        # Inicializar BD en primer uso
        init_db()
        
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
    user = message.from_user
    try:
        # Verificar si ya está registrado
        conn = sqlite3.connect('/app/ecotransportistas.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (user.id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            bot.reply_to(message, 
                "✅ <b>Ya estás registrado en el sistema</b>\n\n"
                "Usa /mis_datos para ver tu información",
                parse_mode='HTML'
            )
        else:
            # Registrar nuevo usuario
            cursor.execute('''
                INSERT INTO usuarios (telegram_id, username, nombre_completo, estado)
                VALUES (?, ?, ?, ?)
            ''', (user.id, user.username, f"{user.first_name} {user.last_name or ''}", "pendiente"))
            
            conn.commit()
            bot.reply_to(message,
                "📝 <b>Registro Iniciado</b>\n\n"
                "✅ Has sido registrado en el sistema\n"
                "📞 Completa tu registro con /mis_datos\n"
                "🔜 Funcionalidades completas próximamente",
                parse_mode='HTML'
            )
            logger.info(f"Nuevo usuario registrado: {user.id}")
            
        conn.close()
    except Exception as e:
        logger.error(f"Error en registro: {e}")
        bot.reply_to(message, "❌ Error en el registro. Intenta nuevamente.")

@bot.message_handler(commands=['mis_datos'])
def show_my_data(message):
    user = message.from_user
    try:
        conn = sqlite3.connect('/app/ecotransportistas.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (user.id,))
        user_data = cursor.fetchone()
        
        if user_data:
            user_info = f"""
👤 <b>Tu Información</b>

🆔 ID: <code>{user_data[1]}</code>
👤 Username: @{user_data[2] or 'No tiene'}
📛 Nombre: {user_data[3]}
📞 Teléfono: {user_data[4] or 'No registrado'}
🚀 Tipo: {user_data[5] or 'No definido'}
🏠 País: {user_data[6]}
📍 Provincia: {user_data[7] or 'No definida'}
🗺️ Zona: {user_data[8] or 'No definida'}
✅ Estado: {user_data[9]}
            """
        else:
            user_info = f"""
👤 <b>Información Básica</b>

🆔 ID: <code>{user.id}</code>
👤 Username: @{user.username or 'No tiene'}
📛 Nombre: {user.first_name} {user.last_name or ''}

📝 <i>Usa /registro para completar tu perfil</i>
            """
        
        bot.reply_to(message, user_info, parse_mode='HTML')
        conn.close()
    except Exception as e:
        logger.error(f"Error en mis_datos: {e}")
        bot.reply_to(message, f"👤 <b>Información Básica</b>\n\n🆔 ID: <code>{user.id}</code>\n👤 Username: @{user.username or 'No tiene'}\n📛 Nombre: {user.first_name}", parse_mode='HTML')

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
    
    try:
        # Obtener estadísticas
        conn = sqlite3.connect('/app/ecotransportistas.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado = 'activo'")
        usuarios_activos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM solicitudes")
        total_solicitudes = cursor.fetchone()[0]
        
        conn.close()
        
        admin_text = f"""
👑 <b>Panel de Administración Suprema</b>

👋 Bienvenido, {user.first_name}

📊 <b>Estadísticas del Sistema:</b>
👥 Total usuarios: {total_usuarios}
✅ Usuarios activos: {usuarios_activos}
📦 Solicitudes: {total_solicitudes}
🌐 Plataforma: Fly.io 24/7
🤖 Estado: <b>OPERATIVO</b>

🔧 <b>Acciones disponibles:</b>
• Ver usuarios registrados
• Gestionar estructura administrativa  
• Monitorear solicitudes
• Configurar comisiones

🚀 <b>Sistema EcoTransportistas 100% Operativo</b>
        """
        bot.reply_to(message, admin_text, parse_mode='HTML')
        logger.info(f"Admin {user.username} accedió al panel")
        
    except Exception as e:
        logger.error(f"Error en admin_panel: {e}")
        bot.reply_to(message, "❌ Error cargando el panel administrativo")

# Manejar mensajes de texto normales
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        return
    
    bot.reply_to(message,
        f"🤖 <b>EcoTransportistas Bot</b>\n\n"
        f"Recibí tu mensaje: <code>{message.text}</code>\n\n"
        f"Usa /ayuda para ver los comandos disponibles.\n"
        f"Usa /start para comenzar.",
        parse_mode='HTML'
    )

# Endpoint de salud para Fly.io
@app.route('/')
def health_check():
    return "✅ EcoTransportistas Bot - OPERATIVO"

# Función principal
def main():
    logger.info("🚀 Iniciando EcoTransportistas Bot en Fly.io...")
    
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
