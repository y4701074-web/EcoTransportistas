import sqlite3
from bot_instance import bot, user_states
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger
import keyboards

# COMANDO NUEVA SOLICITUD
@bot.message_handler(func=lambda message: message.text == "📦 Nueva Solicitud")
def start_new_request(message):
    try:
        user = message.from_user
        user_db = get_user_by_telegram_id(user.id)
            
        if not user_db or user_db['tipo'] not in ['solicitante', 'ambos']:
            bot.reply_to(message, get_message('error_not_solicitante', user.id))
            return
                
        # Iniciar estado de nueva solicitud
        user_states[user.id] = {
            'step': 'request_vehicle_type',
            'request_data': {}
        }
        
        markup = keyboards.get_vehicle_type_keyboard()
        
        bot.send_message(message.chat.id, get_message('request_vehicle_type', user.id),
                        reply_markup=markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error iniciando nueva solicitud: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vehicle_'))
def handle_vehicle_selection(call):
    try:
        user = call.from_user
        if user.id not in user_states: return
        
        vehicle_type = call.data.split('_')[1]
        
        user_states[user.id]['request_data']['vehicle_type'] = vehicle_type
        user_states[user.id]['step'] = 'request_cargo_type'
        
        markup = keyboards.get_cargo_type_keyboard()
        
        bot.edit_message_text(
            get_message('request_cargo_type', user.id),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error selección vehículo: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cargo_'))
def handle_cargo_selection(call):
    try:
        user = call.from_user
        if user.id not in user_states: return

        cargo_type = call.data.split('_')[1]
        
        user_states[user.id]['request_data']['cargo_type'] = cargo_type
        user_states[user.id]['step'] = 'request_description'
        
        bot.edit_message_text(
            get_message('request_description', user.id),
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error selección carga: {e}")
        
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'request_description')
def handle_description_input(message):
    try:
        user = message.from_user
        description = message.text.strip()
        
        if len(description) < 10:
            bot.reply_to(message, "❌ La descripción debe tener al menos 10 caracteres")
            return
            
        user_states[user.id]['request_data']['description'] = description
        user_states[user.id]['step'] = 'request_weight'
        
        bot.send_message(message.chat.id, get_message('request_weight', user.id),
                        parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error procesando descripción: {e}")
        
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'request_weight')
def handle_weight_input(message):
    try:
        user = message.from_user
        weight = message.text.strip()
        
        user_states[user.id]['request_data']['weight'] = weight
        user_states[user.id]['step'] = 'request_pickup'
        
        bot.send_message(message.chat.id, get_message('request_pickup', user.id),
                        parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error procesando peso: {e}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'request_pickup')
def handle_pickup_input(message):
    try:
        user = message.from_user
        pickup = message.text.strip()
        
        if len(pickup) < 5:
            bot.reply_to(message, "❌ La dirección debe ser más específica")
            return
            
        user_states[user.id]['request_data']['pickup'] = pickup
        user_states[user.id]['step'] = 'request_delivery'
        
        bot.send_message(message.chat.id, get_message('request_delivery', user.id),
                        parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error procesando recogida: {e}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'request_delivery')
def handle_delivery_input(message):
    try:
        user = message.from_user
        delivery = message.text.strip()
        
        if len(delivery) < 5:
            bot.reply_to(message, "❌ La dirección debe ser más específica")
            return
            
        user_states[user.id]['request_data']['delivery'] = delivery
        user_states[user.id]['step'] = 'request_budget'
        
        bot.send_message(message.chat.id, get_message('request_budget', user.id),
                        parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error procesando entrega: {e}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'request_budget')
def handle_budget_input(message):
    try:
        user = message.from_user
        budget_text = message.text.strip()
        
        try:
            budget = float(budget_text)
            if budget <= 0:
                raise ValueError
        except ValueError:
            bot.reply_to(message, "❌ Ingresa un presupuesto válido en CUP")
            return
            
        user_states[user.id]['request_data']['budget'] = budget
        user_states[user.id]['step'] = 'request_confirm'
        
        request_data = user_states[user.id]['request_data']
        
        summary = f"""
🚚 *Vehículo:* {request_data['vehicle_type'].replace('_', ' ').title()}
📦 *Carga:* {request_data['cargo_type'].replace('_', ' ').title()}
📝 *Descripción:* {request_data['description']}
⚖️ *Peso/Dimensiones:* {request_data['weight']}
📍 *Recogida:* {request_data['pickup']}
🎯 *Entrega:* {request_data['delivery']}
💰 *Presupuesto:* {budget:.2f} CUP
        """
        
        markup = keyboards.get_request_confirmation_keyboard()
        
        bot.send_message(message.chat.id, get_message('request_summary', user.id, summary=summary),
                        reply_markup=markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error procesando presupuesto: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('publish_'))
def handle_publish_decision(call):
    try:
        user = call.from_user
        
        if call.data == 'publish_no':
            bot.edit_message_text(
                get_message('request_cancelled', user.id),
                call.message.chat.id,
                call.message.message_id
            )
            if user.id in user_states:
                del user_states[user.id]
            return
        
        if user.id not in user_states or 'request_data' not in user_states[user.id]:
            bot.edit_message_text(get_message('error_generic', user.id), call.message.chat.id, call.message.message_id)
            return

        request_data = user_states[user.id]['request_data']
        
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            user_db = get_user_by_telegram_id(user.id)
            
            cursor.execute('''
                INSERT INTO solicitudes (usuario_id, tipo_vehiculo, tipo_carga, descripcion, peso, direccion_desde, direccion_hacia, presupuesto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_db['id'],
                request_data['vehicle_type'],
                request_data['cargo_type'],
                request_data['description'],
                request_data['weight'],
                request_data['pickup'],
                request_data['delivery'],
                request_data['budget']
            ))
            
            solicitud_id = cursor.lastrowid
            
            cursor.execute('''
                SELECT telegram_id FROM usuarios 
                WHERE (tipo = 'transportista' OR tipo = 'ambos') 
                AND provincia = ? AND estado = 'activo'
            ''', (user_db['provincia'],))
            
            transportistas = cursor.fetchall()
            conn.commit()
        
        # Notificar a transportistas
        request_details = f"""
📦 *Nueva Solicitud en tu Zona!* (ID: #{solicitud_id})

🚚 Vehículo: {request_data['vehicle_type'].replace('_', ' ').title()}
📦 Carga: {request_data['cargo_type'].replace('_', ' ').title()}
📝 Descripción: {request_data['description']}
📍 Recogida: {request_data['pickup']}
🎯 Entrega: {request_data['delivery']}
💰 Presupuesto: {request_data['budget']:.2f} CUP
        """
        markup = keyboards.get_accept_request_keyboard(solicitud_id)
        
        for transportista in transportistas:
            try:
                bot.send_message(
                    transportista[0],
                    request_details,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error notificando transportista {transportista[0]}: {e}")
        
        bot.edit_message_text(
            get_message('request_published', user.id),
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        
        if user.id in user_states:
            del user_states[user.id]
            
        log_audit("request_created", user.id, f"Solicitud #{solicitud_id}")
        
    except Exception as e:
        logger.error(f"Error publicando solicitud: {e}")
      
