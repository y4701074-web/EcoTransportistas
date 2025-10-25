# handlers/registro.py
from bot_instance import bot
from config import (
    logger, STATE_WAITING_LANGUAGE, STATE_WAITING_ROLE, STATE_ACTIVE, 
    ROLE_PENDIENTE, ROLE_SOLICITANTE, ROLE_TRANSPORTISTA, ROLE_AMBOS
)
from db import get_user_by_telegram_id, set_user_registration_data, get_user_state, set_user_state
import telebot
import keyboards

@bot.message_handler(commands=['start', 'registro'])
def start_command(message):
    user = message.from_user
    chat_id = message.chat.id
    
    user_data = get_user_by_telegram_id(user.id)
    
    if not user_data:
        # Usuario nuevo - empezar registro
        bot.send_message(
            chat_id, 
            "🚀 ¡Bienvenido a EcoTransportistas! 🌟\n\nVamos a crear tu cuenta.",
            reply_markup=keyboards.get_language_keyboard()
        )
    else:
        # Usuario existente
        if user_data['estado'] == STATE_ACTIVE:
            bot.send_message(
                chat_id,
                "✅ Ya estás registrado. Usa /menu para ver las opciones."
            )
        else:
            # Continuar registro pendiente
            bot.send_message(
                chat_id,
                f"Continúemos con tu registro. Estado actual: {user_data['estado']}"
            )

# Manejar selección de idioma
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_language_selection(call):
    user = call.from_user
    chat_id = call.message.chat.id
    lang = call.data.split('_')[1]  # 'es' o 'en'
    
    # Guardar idioma y pedir nombre
    set_user_registration_data(
        telegram_id=user.id,
        username=user.username,
        name=user.first_name or "Usuario",
        phone="",
        user_type=ROLE_PENDIENTE,
        pais_id=None,
        provincia_id=None,
        zona_id=None,
        lang=lang
    )
    
    set_user_state(user.id, STATE_WAITING_ROLE)
    
    bot.edit_message_text(
        "👤 **Paso 2: Tipo de Usuario**\n\n¿Qué tipo de usuario serás?",
        chat_id,
        call.message.message_id,
        reply_markup=keyboards.get_user_type_keyboard()
    )

# Manejar selección de tipo de usuario
@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def handle_user_type_selection(call):
    user = call.from_user
    chat_id = call.message.chat.id
    user_type = call.data.split('_')[1]  # 'transportista', 'solicitante', 'ambos'
    
    # Mapear a constantes
    type_map = {
        'transportista': ROLE_TRANSPORTISTA,
        'solicitante': ROLE_SOLICITANTE,
        'ambos': ROLE_AMBOS
    }
    
    user_type_db = type_map.get(user_type, ROLE_PENDIENTE)
    
    # Actualizar tipo de usuario
    user_data = get_user_by_telegram_id(user.id)
    if user_data:
        set_user_registration_data(
            telegram_id=user.id,
            username=user.username,
            name=user_data['nombre_completo'],
            phone=user_data['telefono'],
            user_type=user_type_db,
            pais_id=user_data.get('pais_id'),
            provincia_id=user_data.get('provincia_id'),
            zona_id=user_data.get('zona_id'),
            lang=user_data['idioma']
        )
    
    # Pedir país
    bot.edit_message_text(
        "🌍 **Paso 3: Ubicación**\n\nSelecciona tu país de residencia:",
        chat_id,
        call.message.message_id,
        reply_markup=keyboards.get_countries_registration_keyboard()
    )

# Manejar selección de país
@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_country_'))
def handle_country_selection(call):
    user = call.from_user
    chat_id = call.message.chat.id
    
    if call.data == "no_countries":
        bot.answer_callback_query(call.id, "❌ No hay países disponibles. Contacta al administrador.")
        return
        
    country_id = int(call.data.split('_')[2])
    
    # Actualizar usuario con país
    user_data = get_user_by_telegram_id(user.id)
    if user_data:
        set_user_registration_data(
            telegram_id=user.id,
            username=user.username,
            name=user_data['nombre_completo'],
            phone=user_data['telefono'],
            user_type=user_data['tipo'],
            pais_id=country_id,
            provincia_id=None,
            zona_id=None,
            lang=user_data['idioma']
        )
    
    # Pedir provincia
    bot.edit_message_text(
        "📍 **Selecciona tu provincia:**",
        chat_id,
        call.message.message_id,
        reply_markup=keyboards.get_provincias_registration_keyboard(country_id)
    )

# Manejar selección de provincia
@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_prov_'))
def handle_provincia_selection(call):
    user = call.from_user
    chat_id = call.message.chat.id
    
    if call.data == "no_provincias":
        bot.answer_callback_query(call.id, "❌ No hay provincias en este país.")
        return
        
    provincia_id = int(call.data.split('_')[2])
    
    # Actualizar usuario con provincia
    user_data = get_user_by_telegram_id(user.id)
    if user_data:
        set_user_registration_data(
            telegram_id=user.id,
            username=user.username,
            name=user_data['nombre_completo'],
            phone=user_data['telefono'],
            user_type=user_data['tipo'],
            pais_id=user_data['pais_id'],
            provincia_id=provincia_id,
            zona_id=None,
            lang=user_data['idioma']
        )
    
    # Pedir zona
    bot.edit_message_text(
        "🗺️ **Selecciona tu zona/municipio:**",
        chat_id,
        call.message.message_id,
        reply_markup=keyboards.get_zonas_registration_keyboard(provincia_id)
    )

# Manejar selección de zona y finalizar registro
@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_zona_'))
def handle_zona_selection(call):
    user = call.from_user
    chat_id = call.message.chat.id
    
    if call.data == "no_zonas":
        bot.answer_callback_query(call.id, "❌ No hay zonas en esta provincia.")
        return
        
    zona_id = int(call.data.split('_')[2])
    
    # Actualizar usuario con zona y activar
    user_data = get_user_by_telegram_id(user.id)
    if user_data:
        set_user_registration_data(
            telegram_id=user.id,
            username=user.username,
            name=user_data['nombre_completo'],
            phone=user_data['telefono'],
            user_type=user_data['tipo'],
            pais_id=user_data['pais_id'],
            provincia_id=user_data['provincia_id'],
            zona_id=zona_id,
            lang=user_data['idioma']
        )
        
        # Activar usuario
        set_user_state(user.id, STATE_ACTIVE)
    
    # Mensaje de finalización
    bot.edit_message_text(
        "🎉 **¡Registro Completado!** 🎉\n\n"
        "Tu cuenta ha sido creada exitosamente. Ahora puedes usar todas las funciones del bot.\n\n"
        "Usa /menu para ver las opciones disponibles.",
        chat_id,
        call.message.message_id
    )

# Navegación hacia atrás en el registro
@bot.callback_query_handler(func=lambda call: call.data in ['reg_back_country', 'reg_back_prov'])
def handle_registration_back(call):
    user = call.from_user
    chat_id = call.message.chat.id
    user_data = get_user_by_telegram_id(user.id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Error: usuario no encontrado")
        return
        
    if call.data == 'reg_back_country':
        # Volver a selección de país
        bot.edit_message_text(
            "🌍 **Selecciona tu país de residencia:**",
            chat_id,
            call.message.message_id,
            reply_markup=keyboards.get_countries_registration_keyboard()
        )
        
    elif call.data == 'reg_back_prov':
        # Volver a selección de provincia
        if user_data['pais_id']:
            bot.edit_message_text(
                "📍 **Selecciona tu provincia:**",
                chat_id,
                call.message.message_id,
                reply_markup=keyboards.get_provincias_registration_keyboard(user_data['pais_id'])
            )
        else:
            bot.answer_callback_query(call.id, "❌ Error: no hay país seleccionado")