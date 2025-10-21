import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token del bot desde variables de entorno
BOT_TOKEN = os.getenv('BOT_TOKEN', '8405097042:AAF-ytt1h5o-woafNakYGDHcoi1mh_S5pQ8')
ADMIN_SUPREMO = os.getenv('ADMIN_SUPREMO', '@Y_0304')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Mensaje de bienvenida"""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! 👋\n\n"
        f"🤖 <b>EcoTransportistas Bot</b>\n"
        f"Plataforma de conexión entre transportistas y solicitantes\n\n"
        f"⚙️ <b>Estado:</b> Sistema en desarrollo\n"
        f"👑 <b>Admin Supremo:</b> {ADMIN_SUPREMO}\n\n"
        f"Usa /ayuda para ver los comandos disponibles"
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda - Lista de comandos"""
    ayuda_texto = """
🆘 <b>COMANDOS DISPONIBLES</b>

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
