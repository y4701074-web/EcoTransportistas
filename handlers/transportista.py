import sqlite3
from bot_instance import bot, user_states
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger
import keyboards

@bot.message_handler(func=lambda message: message.text == "📦 Ver Solicitudes")
def show_available_requests(message):
    try:
        user = message.from_user
        user_db = get_user_by_telegram_id(user.id)
            
        if not user_db or user_db['tipo'] not in ['transportista', 'ambos']:
            bot.reply_to(message, get_message('error_not_transportista', user.id))
            return
            
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, u.nombre_completo 
                FROM solicitudes s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.estado = 'activa' AND u.provincia = ?
                ORDER BY s.creado_en DESC
                LIMIT 10
            ''', (user_db['provincia'],))
            
            solicitudes = cursor.fetchall()
        
        if not solicitudes:
            bot.reply_to(message, get_message('no_requests_found', user.id))
            return
        
        for solicitud in solicitudes:
            request_details = f"""
📦 *Solicitud #{solicitud[0]}*

👤 Solicitante: {solicitud[13]}
🚚 Vehículo: {solicitud[2].replace('_', ' ').title()}
📦 Carga: {solicitud[3].replace('_', ' ').title()}
📝 Descripción: {solicitud[4]}
⚖️ Peso: {solicitud[5]}
📍 Recogida: {solicitud[6]}
🎯 Entrega: {solicitud[7]}
💰 Presupuesto: {solicitud[8]:.2f} CUP
            """
            markup = keyboards.get_accept_request_keyboard(solicitud[0])
            bot.send_message(message.chat.id, request_details,
                             reply_markup=markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error mostrando solicitudes: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_'))
def handle_request_acceptance(call):
    try:
        user = call.from_user
        solicitud_id = int(call.data.split('_')[1])
        
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Lock de la solicitud (simple)
            cursor.execute("SELECT estado FROM solicitudes WHERE id = ?", (solicitud_id,))
            sol_estado = cursor.fetchone()

            if not sol_estado or sol_estado[0] != 'activa':
                bot.answer_callback_query(call.id, get_message('request_not_available', user.id))
                bot.edit_message_text("Esta solicitud ya fue tomada.", call.message.chat.id, call.message.message_id)
                return

            # Obtener datos de la solicitud y solicitante
            cursor.execute('''
                SELECT s.usuario_id, u.telegram_id as solicitante_telegram_id
                FROM solicitudes s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.id = ?
            ''', (solicitud_id,))
            solicitud_data = cursor.fetchone()
            if not solicitud_data:
                raise Exception("No se encontró el solicitante")

            solicitante_user_id = solicitud_data[0]
            solicitante_telegram_id = solicitud_data[1]

            transportista_db = get_user_by_telegram_id(user.id)
            
            cursor.execute('''
                UPDATE solicitudes 
                SET transportista_asignado = ?, estado = 'pendiente_confirmacion',
                    pending_confirm_until = datetime('now', '+10 minutes')
                WHERE id = ? AND estado = 'activa'
            ''', (transportista_db['id'], solicitud_id))
            
            if cursor.rowcount == 0:
                bot.answer_callback_query(call.id, get_message('request_not_available', user.id))
                return

            conn.commit()
        
        # Notificar al solicitante
        markup = keyboards.get_solicitante_confirmation_keyboard(solicitud_id)
        confirm_text = f"""
✅ *Transportista Interesado!*

🚚 Un transportista (ID: {transportista_db['id']}) ha aceptado tu solicitud #{solicitud_id}
Tienes *10 minutos* para confirmar o rechazar.

*¿Confirmas este transportista?*
        """
        try:
            bot.send_message(solicitante_telegram_id, confirm_text,
                             reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error notificando solicitante {solicitante_telegram_id}: {e}")
        
        bot.answer_callback_query(call.id, get_message('confirmation_sent', user.id))
        bot.edit_message_text(
            f"✅ *Has aceptado la solicitud #{solicitud_id}*\n\n" + get_message('request_accepted', user.id),
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        
        log_audit("request_accepted", user.id, f"Solicitud #{solicitud_id}")
        
    except Exception as e:
        logger.error(f"Error aceptando solicitud: {e}")
               
