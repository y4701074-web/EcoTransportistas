# handlers/registro.py
from bot_instance import bot
from config import (
    logger, 
    # 🚨 CORRECCIÓN: Usamos STATE_... para estados
    STATE_WAITING_LANGUAGE, STATE_WAITING_PHONE, STATE_WAITING_NAME, STATE_WAITING_ROLE, 
    STATE_WAITING_PROVINCIA, STATE_WAITING_ZONAS, STATE_ACTIVE, ROLE_PENDIENTE,
    ROLE_SOLICITANTE, ROLE_TRANSPORTISTA, ROLE_AMBOS, MESSAGES
)
from db import get_db_connection
import telebot

# --- Funciones de Utilidad (Necesarias para el estado persistente) ---
# 🚨 CORRECCIÓN: Uso consistente de 'telegram_id'
def get_user_state(telegram_id):
    conn = get_db_connection()
    # 🚨 CORRECCIÓN: Columna 'telegram_id' en lugar de 'chat_id'
    user = conn.execute("SELECT estado FROM usuarios WHERE telegram_id = ?", (telegram_id,)).fetchone()
    conn.close()
    return user['estado'] if user else None

# 🚨 CORRECCIÓN: Uso consistente de 'telegram_id'
def set_user_state(telegram_id, state):
    conn = get_db_connection()
    # 🚨 CORRECCIÓN: Columna 'telegram_id' en lugar de 'chat_id'
    conn.execute("UPDATE usuarios SET estado = ? WHERE telegram_id = ?", (state, telegram_id))
    conn.commit()
    conn.close()

# --- Handler para /start ---
@bot.message_handler(commands=['start', 'registro'])
def start_command(message):
    telegram_id = message.chat.id
    username = message.from_user.username
    
    conn = get_db_connection()
    # 🚨 CORRECCIÓN: Columna 'telegram_id'
    user = conn.execute("SELECT estado, idioma, tipo FROM usuarios WHERE telegram_id = ?", (telegram_id,)).fetchone()
    conn.close()
    
    if not user:
        # 1. Usuario nuevo: Iniciar flujo y registrar estado inicial
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO usuarios (telegram_id, username, estado, tipo)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, username, STATE_WAITING_LANGUAGE, ROLE_PENDIENTE)) # 🚨 CORRECCIÓN: Columna 'telegram_id'
        conn.commit()
        conn.close()
        
        # 2. Pedir idioma
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("Español 🇪🇸", "English 🇺🇸")
        
        bot.send_message(telegram_id, MESSAGES['es']['choose_language'], 
                         parse_mode="Markdown", reply_markup=markup)
        
    elif user['estado'] == STATE_ACTIVE:
        # Usuario registrado y activo: mostrar menú
        from handlers.general import create_main_menu_keyboard
        # Obtener el idioma para los mensajes
        lang = user['idioma'] if user['idioma'] in MESSAGES else 'es'
        
        markup = create_main_menu_keyboard(user['tipo']) # 'tipo' es el rol
        bot.send_message(telegram_id, MESSAGES[lang]['main_menu'], parse_mode="Markdown", reply_markup=markup)
    else:
        # Estado de registro pendiente: recordar dónde se quedó
        bot.send_message(telegram_id, f"Ya estás en un proceso de registro (Estado: {user['estado']}). Por favor, continúa.")

# --- Flujo de Selección de Idioma (Paso 1) ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_LANGUAGE)
def handle_language_selection(message):
    telegram_id = message.chat.id
    
    if message.text in ["Español 🇪🇸", "English 🇺🇸"]:
        lang = 'es' if "Español" in message.text else 'en'
        
        # 1. Actualizar idioma y estado
        # Aquí se necesita una función en db.py para actualizar idioma, usaremos una temporal
        conn = get_db_connection()
        conn.execute("UPDATE usuarios SET idioma = ? WHERE telegram_id = ?", (lang, telegram_id))
        conn.commit()
        conn.close()
        
        set_user_state(telegram_id, STATE_WAITING_PHONE)
        
        # 2. Pedir número de teléfono
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        # Pedir contacto requiere el mensaje en el idioma seleccionado
        markup.add(telebot.types.KeyboardButton(text=MESSAGES[lang]['registration_start'].split('\n')[1].strip(), request_contact=True))
        
        bot.send_message(telegram_id, MESSAGES[lang]['registration_start'], 
                         parse_mode="Markdown", reply_markup=markup)
        
    else:
        bot.send_message(telegram_id, MESSAGES['es']['choose_language'], parse_mode="Markdown")

# --- Flujo de Teléfono (Paso 2) ---
@bot.message_handler(content_types=['contact'], func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_PHONE)
def handle_phone_received(message):
    telegram_id = message.chat.id
    phone = message.contact.phone_number
    
    # 1. Actualizar teléfono y estado
    conn = get_db_connection()
    conn.execute("UPDATE usuarios SET telefono = ?, estado = ? WHERE telegram_id = ?", (phone, STATE_WAITING_NAME, telegram_id))
    conn.commit()
    conn.close()
    
    # 2. Pedir Nombre
    # Nota: Se asume que el idioma ya está en la DB
    lang = 'es' # Aquí se debería obtener el idioma del usuario de la DB
    
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(telegram_id, MESSAGES[lang]['phone_received'], 
                     parse_mode="Markdown", reply_markup=markup)
    
# --- Flujo de Nombre (Paso 3) ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_NAME)
def handle_name_received(message):
    telegram_id = message.chat.id
    name = message.text
    
    # 1. Actualizar nombre y estado
    conn = get_db_connection()
    conn.execute("UPDATE usuarios SET nombre_completo = ?, estado = ? WHERE telegram_id = ?", (name, STATE_WAITING_ROLE, telegram_id))
    conn.commit()
    conn.close()
    
    # 2. Pedir Rol
    lang = 'es' # Aquí se debería obtener el idioma del usuario de la DB
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(ROLE_SOLICITANTE, ROLE_TRANSPORTISTA)
    markup.add(ROLE_AMBOS)
    
    bot.send_message(telegram_id, MESSAGES[lang]['name_received'], 
                     parse_mode="Markdown", reply_markup=markup)

# --- Flujo de Rol (Paso 4) ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_ROLE)
def handle_role_selection(message):
    telegram_id = message.chat.id
    role = message.text
    
    VALID_ROLES = [ROLE_SOLICITANTE, ROLE_TRANSPORTISTA, ROLE_AMBOS]
    
    if role in VALID_ROLES:
        # 1. Actualizar rol y estado
        conn = get_db_connection()
        conn.execute("UPDATE usuarios SET tipo = ?, estado = ? WHERE telegram_id = ?", (role, STATE_WAITING_PROVINCIA, telegram_id))
        conn.commit()
        conn.close()
        
        # 2. Pedir Provincia (Simulado por ahora, se necesita el módulo de geografía)
        lang = 'es' # Aquí se debería obtener el idioma del usuario de la DB
        
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        # Nota: Aquí deberías cargar los países/provincias desde la DB
        markup.add("Cuba 🇨🇺", "México 🇲🇽") 
        markup.add("➡️ Saltar este paso (País/Provincia)") # Opción de saltar para testing
        
        bot.send_message(telegram_id, MESSAGES[lang]['user_type_selected'].format(role=role), 
                         parse_mode="Markdown", reply_markup=markup)
        
    else:
        bot.send_message(telegram_id, "Opción no válida. Por favor, selecciona uno de los botones.")

# --- Flujo de Finalización (Simulado) ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_PROVINCIA)
def handle_finish_registration_simulated(message):
    telegram_id = message.chat.id
    
    # 1. Finalizar (pasar a activo)
    set_user_state(telegram_id, STATE_ACTIVE)
    
    # 2. Recuperar datos para el resumen
    conn = get_db_connection()
    user_data = conn.execute("SELECT nombre_completo, telefono, tipo FROM usuarios WHERE telegram_id = ?", (telegram_id,)).fetchone()
    conn.close()
    
    # 3. Enviar mensaje de éxito
    lang = 'es' 
    if user_data:
        msg = MESSAGES[lang]['profile_complete'].format(
            name=user_data['nombre_completo'], 
            phone=user_data['telefono'], 
            tipo=user_data['tipo'],
            pais="N/A", # Simulado
            provincia="N/A" # Simulado
        )
        # Mostrar el menú principal
        from handlers.general import create_main_menu_keyboard
        markup = create_main_menu_keyboard(user_data['tipo']) 
        
        bot.send_message(telegram_id, msg, parse_mode="Markdown", reply_markup=markup)

