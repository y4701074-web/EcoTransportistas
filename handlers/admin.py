import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger, ADMIN_SUPREMO

@bot.message_handler(commands=['admin_panel'])
def admin_panel(message):
    try:
        user = message.from_user
        
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.nivel, a.region_asignada 
                FROM administradores a
                JOIN usuarios u ON a.usuario_id = u.id
                WHERE u.telegram_id = ? AND a.estado = 'activo'
            ''', (user.id,))
            
            admin_data = cursor.fetchone()
            
            is_supremo = str(user.id) == ADMIN_SUPREMO
            
            if not admin_data and not is_supremo:
                bot.reply_to(message, get_message('error_no_permission', user.id))
                return
        
            if admin_data:
                nivel = admin_data[0]
                region = admin_data[1]
            else:
                nivel = "supremo"
                region = "Todo Cuba"
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado = 'activo'")
            usuarios_activos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM solicitudes")
            total_solicitudes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado = 'activa'")
            solicitudes_activas = cursor.fetchone()[0]
            
            admin_text = f"""
👑 *Panel de Administración*

*Tu Nivel:* {nivel.title()}
*Tu Región:* {region}

📊 *Estadísticas del Sistema:*
👥 Total usuarios: {total_usuarios}
✅ Usuarios activos: {usuarios_activos}
📦 Total solicitudes: {total_solicitudes}
🟢 Solicitudes activas: {solicitudes_activas}

🔧 *Acciones disponibles:*
• Ver usuarios de tu región
• Gestionar solicitudes
            """
            
            markup = InlineKeyboardMarkup()
            if nivel == "supremo":
                markup.add(InlineKeyboardButton("🌍 Gestionar Admin", callback_data="admin_manage_admins"))
            
            markup.add(InlineKeyboardButton("👥 Ver Usuarios", callback_data="admin_view_users"))
            markup.add(InlineKeyboardButton("📊 Estadísticas Detalladas", callback_data="admin_stats"))
            
            bot.reply_to(message, admin_text, reply_markup=markup, parse_mode='Markdown')
            
            log_audit("admin_panel_accessed", user.id)
            
    except Exception as e:
        logger.error(f"Error en panel admin: {e}")
          
