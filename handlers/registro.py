import sqlite3
from telebot.types import ReplyKeyboardRemove
from bot_instance import bot, user_states
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE
from utils import get_message
from config import logger, PROVINCIAS_CUBA, ZONAS_POR_PROVINCIA
import keyboards
# ELIMINADA LA IMPORTACIÓN CIRCULAR de la cabecera

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user = message.from_user
        user_id = user.id
        
        existing_user = get_user_by_telegram_id(user_id)
            
        if existing_user:
            # Importación local para romper el ciclo
            from .general import show_main_menu 
            
            welcome_text = get_message('welcome', user_id, name=user.first_name)
            bot.reply_to(message, welcome_text, parse_mode='Markdown')
            show_main_menu(message.chat.id, user_id) # Mostrar menú si ya existe
            return
        
        # Si no está registrado, pedir idioma
        markup = keyboards.get_language_keyboard()
        bot.reply_to(message, get_message('choose_language', user_id), 
                    reply_markup=markup, parse_mode='Markdown')
        
        log_audit("start_command", user_id)
        
    except Exception as e:
        logger.error(f"Error en /start: {e}")
        bot.reply_to(message, "❌ Error iniciando el bot. Intenta nuevamente.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_language_selection(call):
    try:
        user = call.from_user
        lang = call.data.split('_')[1]
        
        # Guardar idioma temporalmente
        user_states[user.id] = {'lang': lang, 'step': 'waiting_phone'}
        
        markup = keyboards.get_phone_keyboard()
        
        bot.send_message(call.message.chat.id, get_message('registration_start', user.id),
                        reply_markup=markup, parse_mode='Markdown')
        
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
    except Exception as e:
        logger.error(f"Error selección idioma: {e}")

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    try:
        user = message.from_user
        if user.id not in user_states or user_states[user.id].get('step') != 'waiting_phone':
            return
            
        phone = message.contact.phone_number
        user_states[user.id]['phone'] = phone
        user_states[user.id]['step'] = 'waiting_name'
        
        bot.send_message(message.chat.id, get_message('phone_received', user.id, phone=phone),
                        reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error procesando contacto: {e}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'waiting_name')
def handle_name_input(message):
    try:
        user = message.from_user
        name = message.text.strip()
        
        if len(name) < 2:
            bot.reply_to(message, "❌ El nombre debe tener al menos 2 caracteres")
            return
            
        user_states[user.id]['name'] = name
        user_states[user.id]['step'] = 'waiting_type'
        
        markup = keyboards.get_user_type_keyboard()
        
        bot.send_message(message.chat.id, get_message('choose_user_type', user.id),
                        reply_markup=markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error procesando nombre: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def handle_user_type_selection(call):
    try:
        user = call.from_user
        user_type = call.data.split('_')[1]
        
        user_states[user.id]['type'] = user_type
        user_states[user.id]['step'] = 'waiting_provincia'
        
        markup = keyboards.get_provincias_keyboard()
        
        message_key = f'{user_type}_selected'
        bot.edit_message_text(
            get_message(message_key, user.id),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error selección tipo usuario: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('prov_'))
def handle_provincia_selection(call):
    try:
        user = call.from_user
        provincia_code = call.data.split('_')[1]
        provincia_name = PROVINCIAS_CUBA.get(provincia_code, 'Desconocida')
        
        user_states[user.id]['provincia'] = provincia_code
        user_states[user.id]['step'] = 'waiting_zona'
        
        markup = keyboards.get_zonas_keyboard(provincia_code)
        
        bot.edit_message_text(
            get_message('provincia_selected', user.id, provincia=provincia_name),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error selección provincia: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('zona_'))
def handle_zona_selection(call):
    try:
        user = call.from_user
        zona = call.data.split('_')[1]
        
        user_data = user_states[user.id]
        
        # Guardar usuario en base de datos
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, provincia, zona, idioma)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.id,
                user.username,
                user_data['name'],
                user_data.get('phone', 'N/A'),
                user_data['type'],
                user_data['provincia'],
                zona,
                user_data.get('lang', 'es')
            ))
            conn.commit()
            
        # Mensaje de confirmación
        provincia_name = PROVINCIAS_CUBA.get(user_data['provincia'], 'Desconocida')
        tipo_map = {
            'transportista': 'Transportista',
            'solicitante': 'Solicitante', 
            'ambos': 'Ambos roles'
        }
        
        completion_text = get_message('zona_selected', user.id,
                                    name=user_data['name'],
                                    phone=user_data.get('phone', 'N/A'),
                                    tipo=tipo_map[user_data['type']],
                                    provincia=provincia_name,
                                    zona=zona)
        
        bot.edit_message_text(
            completion_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        
        # Importación local para romper el ciclo
        from .general import show_main_menu 
        
        # Mostrar menú de acciones
        show_main_menu(call.message.chat.id, user.id)
        
        # Limpiar estado
        if user.id in user_states:
            del user_states[user.id]
            
        log_audit("user_registered", user_id, f"Tipo: {user_data['type']}")
        
    except Exception as e:
        logger.error(f"Error completando registro: {e}")
