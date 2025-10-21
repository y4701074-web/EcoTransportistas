import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configuración logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8405097042:AAF-ytt1h5o-woafNakYGDHcoi1mh_S5pQ8')
ADMIN_SUPREMO = os.environ.get('ADMIN_SUPREMO', '@Y_0304')
PORT = int(os.environ.get('PORT', 8443))

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('ecotransportistas.db')
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
    
    conn.commit()
    conn.close()
    logger.info("✅ Base de datos inicializada")

# Comandos del bot
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    await update.message.reply_html(
        f"🚀 <b>¡Bienvenido a EcoTransportistas!</b>\n\n"
        f"👋 Hola {user.mention_html()}\n\n"
        f"🌍 <i>Conectando transportistas y solicitantes en Cuba</i>\n\n"
        f"📝 Usa /registro para comenzar\n"
        f"🆘 Usa /ayuda para ver todos los comandos"
    )

async def ayuda(update: Update, context: CallbackContext):
    ayuda_texto = """
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
    await update.message.reply_html(ayuda_texto)

async def registro(update: Update, context: CallbackContext):
    await update.message.reply_html(
        "📝 <b>Registro de Usuario</b>\n\n"
        "🔜 <i>Esta funcionalidad estará disponible muy pronto</i>\n\n"
        "Mientras tanto, puedes:\n"
        "• Explorar los comandos con /ayuda\n"
        "• Contactar al administrador: @Y_0304"
    )

async def mis_datos(update: Update, context: CallbackContext):
    user = update.effective_user
    await update.message.reply_html(
        f"👤 <b>Tu Información</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Username: @{user.username if user.username else 'No tiene'}\n"
        f"📛 Nombre: {user.first_name} {user.last_name or ''}\n\n"
        f"🔜 <i>Registro completo disponible próximamente</i>"
    )

async def admin_panel(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.username != ADMIN_SUPREMO.replace('@', ''):
        await update.message.reply_html(
            "❌ <b>Acceso Denegado</b>\n\n"
            "Solo el administrador supremo puede acceder a este panel."
        )
        return
    
    await update.message.reply_html(
        f"👑 <b>Panel de Administración Suprema</b>\n\n"
        f"👋 Bienvenido, {user.mention_html()}\n\n"
        f"📊 <b>Estado del Sistema:</b>\n"
        f"✅ Bot: Operativo\n"
        f"🗄️ Base de datos: Inicializada\n"
        f"🌐 Plataforma: Railway\n"
        f"👥 Usuarios registrados: Próximamente\n\n"
        f"🔧 <b>Acciones disponibles:</b>\n"
        f"• Configurar estructura administrativa\n"
        f"• Gestionar usuarios\n"
        f"• Ver estadísticas\n\n"
        f"🔜 <i>Panel completo en desarrollo</i>"
    )

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    await update.message.reply_html(
        f"🤖 <b>EcoTransportistas Bot</b>\n\n"
        f"Recibí tu mensaje: <code>{text}</code>\n\n"
        f"Usa /ayuda para ver los comandos disponibles."
    )

def main():
    # Inicializar base de datos
    init_db()
    
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("registro", registro))
    application.add_handler(CommandHandler("mis_datos", mis_datos))
    application.add_handler(CommandHandler("admin_panel", admin_panel))
    
    # Manejar mensajes de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Configuración específica para Railway
    webhook_url = os.environ.get('RAILWAY_STATIC_URL')
    
    if webhook_url:
        # Modo webhook para Railway
        logger.info("🚀 Iniciando en modo WEBHOOK (Railway)")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{webhook_url}/{BOT_TOKEN}"
        )
    else:
        # Modo polling para desarrollo local
        logger.info("🔧 Iniciando en modo POLLING (Desarrollo)")
        application.run_polling()

if __name__ == '__main__':
    logger.info("🚀 Iniciando EcoTransportistas Bot...")
    main()
<b>Para Usuarios:</b>
/start - Iniciar el bot
/ayuda - Mostrar esta ayuda
/registro - Registrarse en el sistema
/mis_datos - Ver información del perfil

<b>Para Administradores:</b>
/admin_panel - Panel de control administrativo

<b>Sistema en Desarrollo:</b>
Próximamente: Solicitudes, pagos, reportes, etc.
    """
    await update.message.reply_html(ayuda_texto)

async def registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /registro - Iniciar proceso de registro"""
    await update.message.reply_html(
        "📝 <b>REGISTRO EN EL SISTEMA</b>\n\n"
        "El sistema de registro estará disponible pronto.\n"
        "Actualmente estamos implementando:\n"
        "✅ Base de datos SQLite\n"
        "✅ Sistema de usuarios\n"
        "✅ Jerarquía administrativa\n\n"
        "⏳ <i>Próxima actualización: Módulo de registro completo</i>"
    )

async def mis_datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /mis_datos - Mostrar información del usuario"""
    user = update.effective_user
    await update.message.reply_html(
        f"👤 <b>INFORMACIÓN DE PERFIL</b>\n\n"
        f"🆔 <b>ID:</b> {user.id}\n"
        f"👤 <b>Nombre:</b> {user.first_name}\n"
        f"📛 <b>Username:</b> @{user.username if user.username else 'No tiene'}\n"
        f"📞 <b>Teléfono:</b> Próximamente\n\n"
        f"📊 <b>Estado:</b> No registrado\n"
        f"🎯 <b>Rol:</b> Por definir\n\n"
        f"<i>Usa /registro para completar tu perfil</i>"
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /admin_panel - Panel de administración"""
    user = update.effective_user
    if str(user.username).lower() == 'y_0304':
        await update.message.reply_html(
            f"👑 <b>PANEL DE ADMINISTRACIÓN SUPREMO</b>\n\n"
            f"👤 <b>Usuario:</b> {user.mention_html()}\n"
            f"🎯 <b>Nivel:</b> Admin Supremo\n\n"
            f"⚙️ <b>Funciones disponibles próximamente:</b>\n"
            f"• Gestión de usuarios\n"
            f"• Configuración de comisiones\n"
            f"• Sistema de reportes\n"
            f"• Auditoría del sistema\n\n"
            f"🔄 <i>En desarrollo</i>"
        )
    else:
        await update.message.reply_html(
            "❌ <b>ACCESO DENEGADO</b>\n\n"
            "No tienes permisos de administrador.\n"
            "Contacta a @Y_0304 para más información."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar mensajes de texto normales"""
    text = update.message.text
    if not text.startswith('/'):
        await update.message.reply_html(
            "🤖 <b>EcoTransportistas Bot</b>\n\n"
            "Escribe /start para comenzar\n"
            "Escribe /ayuda para ver comandos disponibles"
        )

def main():
    """Función principal del bot"""
    print("🚀 Iniciando EcoTransportistas Bot...")
    
    # Crear la aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Añadir manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("registro", registro))
    application.add_handler(CommandHandler("mis_datos", mis_datos))
    application.add_handler(CommandHandler("admin_panel", admin_panel))
    
    # Manejar mensajes de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Iniciar el bot
    print("✅ Bot iniciado correctamente")
    print("🤖 Busca tu bot en Telegram y escribe /start")
    application.run_polling()

if __name__ == "__main__":
    main()
