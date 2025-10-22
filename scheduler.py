import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from bot_instance import bot
from db import DATABASE_FILE
from config import logger
from utils import get_message

def check_expired_requests():
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Buscar solicitudes pendientes y al solicitante
            cursor.execute('''
                SELECT s.id, u.telegram_id 
                FROM solicitudes s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.estado = 'pendiente_confirmacion' 
                AND s.pending_confirm_until < datetime('now')
            ''')
            
            expired_requests = cursor.fetchall()
            
            for request in expired_requests:
                request_id, solicitante_telegram_id = request
                
                # Reactivar solicitud
                cursor.execute('''
                    UPDATE solicitudes 
                    SET estado = 'activa', transportista_asignado = NULL, pending_confirm_until = NULL
                    WHERE id = ?
                ''', (request_id,))
                
                # Notificar al solicitante
                try:
                    bot.send_message(
                        solicitante_telegram_id,
                        get_message('request_expired', solicitante_telegram_id, id=request_id),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error notificando expiración a {solicitante_telegram_id}: {e}")
            
            conn.commit()
            
        if len(expired_requests) > 0:
            logger.info(f"Verificadas solicitudes expiradas: {len(expired_requests)} reactivadas")
    except Exception as e:
        logger.error(f"Error verificando solicitudes expiradas: {e}")

# INICIALIZAR SCHEDULER
def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_expired_requests,
        'interval',
        minutes=1
    )
    scheduler.start()
    logger.info("✅ Scheduler iniciado")
      
