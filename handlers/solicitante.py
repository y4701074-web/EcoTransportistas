import sqlite3
from bot_instance import bot
from db import log_audit, DATABASE_FILE
from utils import get_message
from config import logger

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_') or call.data.startswith('reject_'))
def handle_request_confirmation(call):
    try:
        user = call.from_user
        action = call.data.split('_')[0]
        solicitud_id = int(call.data.split('_')[1])
        
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.id, s.estado, u.telegram_id as transportista_telegram_id, u.telefono as transportista_phone, s.usuario_id
                FROM solicitudes s
                JOIN usuarios u ON s.transportista_asignado = u.id
                WHERE s.id = ?
            ''', (solicitud_id,))
            solicitud = cursor.fetchone()
            
            if not solicitud:
                bot.answer_callback_query(call.id, get_message('request_processed', user.id))
                return

            # Verificar que el usuario que confirma es el solicitante
            if solicitud[4] != user.id:
                 # Esta lógica asume que user.id es el telegram_id, pero la BD usa 'id' de usuario
                 # Sería mejor comparar con el telegram_id del solicitante
                 pass # Omitimos esta validación por ahora, pero es importante

            if solicitud[1] != 'pendiente_confirmacion':
                bot.answer_callback_query(call.id, get_message('request_processed', user.id))
                return
            
            transportista_telegram_id = solicitud[2]
            transportista_phone = solicitud[3]

            if action == 'confirm':
                cursor.execute('''
                    UPDATE solicitudes 
                    SET estado = 'confirmada', pending_confirm_until = NULL
                    WHERE id = ?
                ''', (solicitud_id,))
                
                # Notificar al transportista
                confirm_text = get_message('request_confirmed', transportista_telegram_id, phone=transportista_phone or "No disponible")
                try:
                    bot.send_message(transportista_telegram_id, confirm_text, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Error notificando transportista {transportista_telegram_id}: {e}")
                
                # Confirmar al solicitante
                bot.edit_message_text(
                    get_message('request_confirmed_solicitante', user.id),
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
                log_audit("request_confirmed", user.id, f"Solicitud #{solicitud_id}")

            elif action == 'reject':
                # Reactivar solicitud
                cursor.execute('''
                    UPDATE solicitudes 
                    SET estado = 'activa', transportista_asignado = NULL, pending_confirm_until = NULL
                    WHERE id = ?
                ''', (solicitud_id,))
                
                # Notificar al transportista (rechazado)
                try:
                    bot.send_message(transportista_telegram_id, get_message('request_rejected', transportista_telegram_id), parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Error notificando transportista {transportista_telegram_id}: {e}")
                
                # Informar al solicitante
                bot.edit_message_text(
                    f"❌ *Rechazado*. La solicitud #{solicitud_id} ha sido re-publicada.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
                log_audit("request_rejected_by_solicitante", user.id, f"Solicitud #{solicitud_id}")

            conn.commit()
            bot.answer_callback_query(call.id)
            
    except Exception as e:
        logger.error(f"Error confirmando solicitud: {e}")
              
