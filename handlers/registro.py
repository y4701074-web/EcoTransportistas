# handlers/registro.py
from bot_instance import bot
from config import logger, STATE_WAITING_LANGUAGE, STATE_WAITING_ROLE, STATE_WAITING_PROVINCIA, STATE_WAITING_ZONAS, STATE_ACTIVE, ROLE_SOLICITANTE, ROLE_TRANSPORTISTA, ROLE_AMBOS
from db import get_db_connection
import telebot

# --- Funciones de Utilidad (Deberían estar en un módulo 'utils') ---
def get_user_state(chat_id):
    conn = get_db_connection()
    user = conn.execute("SELECT estado FROM usuarios WHERE chat_id = ?", (chat_id,)).fetchone()
    conn.close()
    return user['estado'] if user else None

def set_user_state(chat_id, state):
    conn = get_db_connection()
    conn.execute("UPDATE usuarios SET estado = ? WHERE chat_id = ?", (state, chat_id))
    conn.commit()
    conn.close()
# --- Fin Funciones de Utilidad ---

# Handler para /start - Inicia el flujo
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    
    conn = get_db_connection()
    user = conn.execute("SELECT estado FROM usuarios WHERE chat_id = ?", (chat_id,)).fetchone()
    conn.close()
    
    if not user:
        # Insertar registro inicial con estado WAIT_LANG
        conn = get_db_connection()
        conn.execute("INSERT INTO usuarios (chat_id, username, estado) VALUES (?, ?, ?)", 
                     (chat_id, message.chat.username, STATE_WAITING_LANGUAGE))
        conn.commit()
        conn.close()

        # 2. ACCIÓN: Selección de idioma (ES/EN)
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("Español 🇪🇸", "English 🇬🇧")
        bot.send_message(chat_id, "¿Qué idioma prefieres? / Which language do you prefer?", reply_markup=markup)
        
    elif user['estado'] != STATE_ACTIVE:
        bot.send_message(chat_id, f"Tu registro está en curso. Por favor, completa el paso actual: {user['estado']}.")
    else:
        bot.send_message(chat_id, "¡Ya estás registrado y activo! Usa /menu.")


# Flujo para la Elección de Rol (Paso 5)
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == 'WAIT_PHONE' or get_user_state(m.chat.id) == 'WAIT_NAME') # Placeholder
# Deberías cambiar 'WAIT_NAME' y 'WAIT_PHONE' por el estado real antes de elegir rol
def handle_role_prompt(message):
    chat_id = message.chat.id
    set_user_state(chat_id, STATE_WAITING_ROLE) # Mover a este estado después de Nombre/Teléfono

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row("📦 Solo Solicitante")
    markup.row("🚚 Solo Transportista")
    markup.row("🔄 Ambos (Solicitante + Transportista)")
    
    bot.send_message(chat_id, "Paso 5: ¿Cuál será tu rol principal en el sistema?", reply_markup=markup)

@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_ROLE)
def handle_role_selection(message):
    chat_id = message.chat.id
    text = message.text
    
    role = None
    if 'solicitante' in text.lower():
        role = ROLE_SOLICITANTE
    elif 'transportista' in text.lower() and 'solo' in text.lower():
        role = ROLE_TRANSPORTISTA
    elif 'ambos' in text.lower() or '🔄' in text:
        role = ROLE_AMBOS # CORRECCIÓN IMPLEMENTADA: Manejo del rol Ambos

    if role:
        conn = get_db_connection()
        conn.execute("UPDATE usuarios SET rol = ? WHERE chat_id = ?", (role, chat_id))
        conn.commit()
        conn.close()
        
        # 6. CONFIGURACIÓN BÁSICA OPCIONAL: Provincia
        set_user_state(chat_id, STATE_WAITING_PROVINCIA)
        
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("➡️ Saltar este paso (Provincia)") 
        
        msg = f"Rol ({role}) registrado. Ahora, **opcionalmente**, selecciona tu provincia base o salta este paso."
        bot.send_message(chat_id, msg, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Opción no válida. Por favor, selecciona uno de los botones.")


# Flujo para Zonas Opcionales (Paso 6)
@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_PROVINCIA)
def handle_provincia_selection(message):
    chat_id = message.chat.id
    
    if message.text == "➡️ Saltar este paso (Provincia)":
        # Saltar Provincia. Pasar a la opción de Zonas.
        set_user_state(chat_id, STATE_WAITING_ZONAS)
        
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("➡️ Saltar este paso (Zonas)") 
        
        bot.send_message(chat_id, "Provincia omitida. Ahora, **opcionalmente**, selecciona tus zonas base o salta este paso.", reply_markup=markup)
        return

    # Si NO salta, registrar provincia y avanzar a Zonas.
    # ... Lógica para registrar provincia ...
    set_user_state(chat_id, STATE_WAITING_ZONAS)
    bot.send_message(chat_id, "Provincia registrada. Continúa con las Zonas.")


@bot.message_handler(func=lambda m: get_user_state(m.chat.id) == STATE_WAITING_ZONAS)
def handle_zonas_selection(message):
    chat_id = message.chat.id
    
    if message.text == "➡️ Saltar este paso (Zonas)":
        # Se omitió la provincia y las zonas.
        pass
    # else:
        # ... Lógica para registrar zonas ...

    # 7. ACTIVACIÓN: Usuario operativo en sistema
    set_user_state(chat_id, STATE_ACTIVE)
    
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "✅ **¡Registro completado!** Eres un usuario activo. Usa /menu.", reply_markup=markup)
