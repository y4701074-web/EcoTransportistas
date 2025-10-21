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
                tipo TEXT DEFAULT 'usuario',
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
🚀 *¡Bienvenido a EcoTransportistas!* 🌟

👋 Hola {user.first_name}!

🌍 *¿Qué es EcoTransportistas?*
Es tu plataforma para conectar *transportistas* con *personas que necesitan enviar cosas* en toda Cuba.

📦 *¿Eres Solicitante?* → Encuentra transporte rápido y confiable
🚚 *¿Eres Transportista?* → Consigue más clientes en tu zona

🛠️ *¿Cómo empezar?*
1️⃣ Usa /registro para crear tu perfil
2️⃣ Elige tu tipo de usuario  
3️⃣ ¡Comienza a conectar!

📋 *Comandos disponibles:*
/ayuda - Ver todos los comandos
/registro - Completar tu registro
/mis_datos - Ver tu información
/admin_panel - Solo administradores

🤝 *¿Problemas o dudas?*
Contacta a: @Y_0304

*¡Conectando Cuba, un transporte a la vez!* 🇨🇺
        """
        bot.reply_to(message, welcome_text, parse_mode='Markdown')
        logger.info(f"Usuario {user.id} usó /start")
        
        # Inicializar BD en primer uso
        init_db()
        
    except Exception as e:
        logger.error(f"Error en /start: {e}")

@bot.message_handler(commands=['ayuda'])
def send_help(message):
    help_text = """
🆘 *COMANDOS DISPONIBLES*

👤 *Para Usuarios:*
/start - Iniciar el bot
/ayuda - Mostrar esta ayuda  
/registro - Registrarse en el sistema
/mis_datos - Ver mi información

👑 *Para Administradores:*
/admin_panel - Panel de control administrativo

🚀 *Próximamente:*
/nueva_solicitud - Publicar nueva solicitud
/ver_solicitudes - Ver solicitudes disponibles
/mis_zonas - Configurar zonas de trabajo
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['registro'])
def start_registration(message):
    user = message.from_user
    try:
        conn = sqlite3.connect('/app/ecotransportistas.db')
        cursor = conn.cursor()
        
        # Verificar si ya está registrado
        cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (user.id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            bot.reply_to(message, 
                "✅ *Ya estás registrado en el sistema*\n\n"
                "Usa /mis_datos para ver tu información",
                parse_mode='Markdown'
            )
        else:
            # Registrar nuevo usuario
            cursor.execute('''
                INSERT INTO usuarios (telegram_id, username, nombre_completo, tipo, estado)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.id, user.username, f"{user.first_name} {user.last_name or ''}", "pendiente", "activo"))
            
            conn.commit()
            bot.reply_to(message,
                "✅ *¡Registro Exitoso!*\n\n"
                f"👤 *Nombre:* {user.first_name}\n"
                f"🆔 *ID:* {user.id}\n"
                f"📝 *Estado:* Registro básico completado\n\n"
                "*Próximos pasos:*\n"
                "• Completa tu perfil con /mis_datos\n"
                "• Elige tu tipo de usuario (Transportista/Solicitante)\n"
                "• ¡Comienza a usar el sistema!",
                parse_mode='Markdown'
            )
            logger.info(f"Nuevo usuario registrado: {user.id} - {user.username}")
            
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
👤 *Tu Información Completa*

🆔 *ID:* {user_data[1]}
👤 *Username:* @{user_data[2] or 'No tiene'}
📛 *Nombre:* {user_data[3]}
📞 *Teléfono:* {user_data[4] or 'Por completar'}
🚀 *Tipo:* {user_data[5]}
🏠 *País:* {user_data[6]}
📍 *Provincia:* {user_data[7] or 'Por completar'}
🗺️ *Zona:* {user_data[8] or 'Por completar'}
✅ *Estado:* {user_data[9]}
📅 *Registrado:* {user_data[10]}

*Para actualizar tu información, contacta a @Y_0304*
            """
        else:
            user_info = f"""
👤 *Información Básica*

🆔 *ID:* {user.id}
👤 *Username:* @{user.username or 'No tiene'}
📛 *Nombre:* {user.first_name} {user.last_name or ''}

📝 *Usa /registro para completar tu perfil en el sistema*
            """
        
        bot.reply_to(message, user_info, parse_mode='Markdown')
        conn.close()
    except Exception as e:
        logger.error(f"Error en mis_datos: {e}")
        bot.reply_to(message, f"👤 *Información Básica*\n\n🆔 *ID:* {user.id}\n👤 *Username:* @{user.username or 'No tiene'}\n📛 *Nombre:* {user.first_name}", parse_mode='Markdown')

@bot.message_handler(commands=['admin_panel'])
def admin_panel(message):
    user = message.from_user
    if user.username != ADMIN_SUPREMO.replace('@', ''):
        bot.reply_to(message,
            "❌ *Acceso Denegado*\n\n"
            "Solo el administrador supremo puede acceder a este panel.",
            parse_mode='Markdown'
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
👑 *Panel de Administración Suprema*

👋 Bienvenido, {user.first_name}

📊 *Estadísticas del Sistema:*
👥 Total usuarios: {total_usuarios}
✅ Usuarios activos: {usuarios_activos}
📦 Solicitudes: {total_solicitudes}
🌐 Plataforma: Fly.io 24/7
🤖 Estado: *OPERATIVO*

🔧 *Acciones disponibles:*
• Ver usuarios registrados
• Gestionar estructura administrativa  
• Monitorear solicitudes
• Configurar comisiones

🚀 *Sistema EcoTransportistas 100% Operativo*
        """
        bot.reply_to(message, admin_text, parse_mode='Markdown')
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
        f"🤖 *EcoTransportistas Bot*\n\n"
        f"Recibí tu mensaje: {message.text}\n\n"
        f"Usa /ayuda para ver los comandos disponibles.\n"
        f"Usa /start para comenzar.",
        parse_mode='Markdown'
    )

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
