# handlers/registro.py (CORREGIDO)
from bot_instance import bot
from config import (
    logger, 
    STATE_WAITING_LANGUAGE, STATE_WAITING_ROLE, STATE_WAITING_PROVINCIA, 
    STATE_WAITING_ZONAS, STATE_ACTIVE, ROLE_PENDIENTE,
    ROLE_SOLICITANTE, ROLE_TRANSPORTISTA, ROLE_AMBOS
)
from db import get_db_connection
import telebot
# Importamos keyboards para el /start, si no está definido en general
import keyboards # Asumiendo que keyboards.py existe e incluye get_language_keyboard

# --- Funciones de Utilidad (Necesarias para el estado persistente) ---
def get_user_state(chat_id):
    conn = get_db_connection()
    # 🚨 CORREGIDO: Usar 'telegram_id' en lugar de 'chat_id'
    user = conn.execute("SELECT estado FROM usuarios WHERE telegram_id = ?", (chat_id,)).fetchone()
    conn.close()
    return user['estado'] if user else None

def set_user_state(chat_id, state):
    conn = get_db_connection()
    # 🚨 CORREGIDO: Usar 'telegram_id' en lugar de 'chat_id'
    conn.execute("UPDATE usuarios SET estado = ? WHERE telegram_id = ?", (state, chat_id))
    conn.commit()
    conn.close()

# --- Handler para /start ---
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id

    conn = get_db_connection()
    # 🚨 CORREGIDO: Usar 'telegram_id' en lugar de 'chat_id'
    user = conn.execute("SELECT estado FROM usuarios WHERE telegram_id = ?", (chat_id,)).fetchone()
    conn.close()

    if not user:
        # 1. Usuario nuevo: Iniciar flujo
        conn = get_db_connection()
        conn.execute("""
            -- 🚨 CORREGIDO: Usar 'telegram_id' en lugar de 'chat_id'
            INSERT INTO usuarios (telegram_id, username, estado, tipo) 
            VALUES (?, ?, ?, ?)
        """, (chat_id, message.chat.username, STATE_WAITING_LANGUAGE, ROLE_PENDIENTE)) # rol cambiado a 'tipo' para coincidir con la tabla
        conn.commit()
        conn.close()

        # Usando el teclado del archivo keyboards.py para consistencia
        # Si usas telebot.types.ReplyKeyboardMarkup, puedes mantenerlo, pero se recomienda usar keyboards.py si existe.
        try:
             # Si usas teclados Inline (como sugiere keyboards.py)
            markup = keyboards.get_language_keyboard()
            bot.send_message(chat_id, "👋 ¡Bienvenido! ¿Qué idioma prefieres? / Which language do you prefer?", reply_markup=markup)
        except NameError:
             # Fallback si keyboards.py no existe o no tiene la función
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add("Español 🇪🇸", "English 🇬🇧")
            bot.send_message(chat_id, "👋 ¡Bienvenido! ¿Qué idioma prefieres? / Which language do you prefer?", reply_markup=markup)

    elif user['estado'] == STATE_ACTIVE:
        # 3. Usuario activo
        # NOTA: Deberías importar y usar el menú principal aquí, por ejemplo:
        # from handlers.general import send_main_menu
        # send_main_menu(message)
        bot.send_message(chat_id, "¡Ya estás registrado y activo! Usa /menu para ver tus opciones.")

    else:
        # Lógica de Reinicio/Continuación: Si el registro quedó a medias
        msg = f"Tu registro quedó pendiente. Estado actual: **{user['estado']}**."

        if user['estado'] == STATE_WAITING_LANGUAGE:
             msg += "\n\nPor favor, selecciona tu idioma nuevamente para comenzar."
             # Usando el mismo markup del flujo de registro
             try:
                 markup = keyboards.get_language_keyboard()
             except NameError:
                 markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                 markup.add("Español 🇪🇸", "English 🇬🇧")

             bot.send_message(chat_id, msg, reply_markup=markup)
             
        # Nota: En un flujo completo, aquí se manejarían los estados WAIT_NAME, WAIT_PHONE, etc.
        elif user['estado'] == STATE_WAITING_ROLE:
            from handlers.general import handle_role_prompt # Se importa la función que genera el teclado de roles
            # Usar la función importada para regenerar el teclado de rol
            handle_role_prompt(message) 
        else:
            bot.send_message(chat_id, msg + "\n\nPor favor, continúa con el paso de registro que te corresponde.")


# --- Flujo de Registro 1: Idioma ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_LANGUAGE)
def handle_language_selection(message):
    chat_id = message.chat.id
    lang = 'ES' if 'español' in message.text.lower() else 'EN'

    conn = get_db_connection()
    # 🚨 CORREGIDO: Usar 'telegram_id' en lugar de 'chat_id'
    # Se actualiza el estado al siguiente paso (WAIT_NAME)
    conn.execute("UPDATE usuarios SET idioma = ?, estado = ? WHERE telegram_id = ?", 
                 (lang, 'WAIT_NAME', chat_id)) 
    conn.commit()
    conn.close()

    set_user_state(chat_id, 'WAIT_NAME')
    bot.send_message(chat_id, "Idioma guardado. Por favor, envíame tu nombre completo.", reply_markup=telebot.types.ReplyKeyboardRemove())

# --- Lógica de Rol (Simulación de estado WAIT_NAME -> WAIT_ROLE) ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == 'WAIT_NAME')
def handle_name_and_move_to_role(message):
    # Simulación de que ya recibimos nombre y pasamos a rol
    from handlers.general import handle_role_prompt

    conn = get_db_connection()
    # 🚨 CORREGIDO: Usar 'telegram_id' en lugar de 'chat_id' y 'nombre_completo' en lugar de 'nombre'
    conn.execute("UPDATE usuarios SET nombre_completo = ?, estado = ? WHERE telegram_id = ?", 
                 (message.text, STATE_WAITING_ROLE, message.chat.id))
    conn.commit()
    conn.close()

    handle_role_prompt(message) # Llama a la función que pide el rol

# --- Flujo de Rol (Paso 5) ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_ROLE)
def handle_role_selection(message):
    chat_id = message.chat.id
    text = message.text

    role = None
    if 'solo solicitante' in text.lower():
        role = ROLE_SOLICITANTE
    elif 'solo transportista' in text.lower():
        role = ROLE_TRANSPORTISTA
    elif 'ambos' in text.lower() or '🔄' in text:
        role = ROLE_AMBOS

    if role:
        conn = get_db_connection()
        # 🚨 CORREGIDO: Usar 'telegram_id' en lugar de 'chat_id' y 'tipo' en lugar de 'rol'
        conn.execute("UPDATE usuarios SET tipo = ? WHERE telegram_id = ?", (role, chat_id))
        conn.commit()
        conn.close()

        # 6. CONFIGURACIÓN BÁSICA OPCIONAL: Provincia
        set_user_state(chat_id, STATE_WAITING_PROVINCIA)

        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("➡️ Saltar este paso (Provincia)") 

        msg = f"Rol ({role}) registrado.\n\n**OPCIONAL:** Selecciona tu provincia base o salta este paso."
        bot.send_message(chat_id, msg, reply_markup=markup)

    else:
        bot.send_message(chat_id, "Opción no válida. Por favor, selecciona uno de los botones.")


# --- Flujo de Zonas Opcionales (Paso 6) ---
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_PROVINCIA)
def handle_provincia_selection(message):
    chat_id = message.chat.id

    if message.text == "➡️ Saltar este paso (Provincia)":
        pass # No se hace nada en la DB, solo se avanza
    else:
         # Lógica para registrar provincia (se necesita un ID válido)
         pass

    set_user_state(chat_id, STATE_WAITING_ZONAS)

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("➡️ Saltar este paso (Zonas)") 

    msg = "Configuración de Provincia gestionada.\n\n**OPCIONAL:** Puedes seleccionar zonas específicas o salta para terminar."
    bot.send_message(chat_id, msg, reply_markup=markup)


@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_ZONAS)
def handle_zonas_selection(message):
    chat_id = message.chat.id

    # 7. ACTIVACIÓN: Usuario operativo en sistema
    set_user_state(chat_id, STATE_ACTIVE)

    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "✅ **¡Registro completado!** Eres un usuario activo. Usa /menu.", reply_markup=markup)
