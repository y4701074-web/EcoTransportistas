import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from bot_instance import bot, user_states
from db import log_audit, get_user_by_telegram_id, DATABASE_FILE, get_admin_data
from utils import get_message
from config import logger
ADMIN_SUPREMO_ID, ADMIN_SUPREMO
import keyboards
import geography_db # Nueva dependencia


# ESTADOS FSM PARA EL FLUJO DE ADMINISTRACIÓN
ADMIN_FSM = {
    'start': 'admin_start',
    'crear_pais_nombre': 'admin_crear_pais_nombre',
    'crear_pais_codigo': 'admin_crear_pais_codigo',
    'crear_prov_select_pais': 'admin_crear_prov_select_pais',
    'crear_prov_nombre': 'admin_crear_prov_nombre',
    'crear_zona_select_prov': 'admin_crear_zona_select_prov',
    'crear_zona_nombre': 'admin_crear_zona_nombre',
    'designar_admin_id': 'admin_designar_admin_id',
    'designar_admin_select_level': 'admin_designar_admin_select_level',
    'designar_admin_select_region': 'admin_designar_admin_select_region', # Guarda el ID del país/provincia/zona
}

def get_admin_main_menu_keyboard(nivel):
    """Genera el teclado principal del panel de administración."""
    markup = InlineKeyboardMarkup(row_width=1)

    # Menú de Creación Geográfica (Abierto al Supremo/Supremo 2 y admins regionales)
    if nivel in ('supremo', 'supremo_2'):
        markup.add(InlineKeyboardButton("🌍 Crear País", callback_data="admin_create_country"))
        
    if nivel in ('supremo', 'supremo_2', 'pais'):
        markup.add(InlineKeyboardButton("📍 Crear Provincia", callback_data="admin_create_provincia"))
        
    if nivel in ('supremo', 'supremo_2', 'pais', 'provincia'):
        markup.add(InlineKeyboardButton("🗺️ Crear Zona/Municipio", callback_data="admin_create_zona"))

    # Menú de Gestión de Admins (Solo Supremo/Supremo 2)
    if nivel in ('supremo', 'supremo_2'):
        markup.add(InlineKeyboardButton("👑 Gestionar Administradores", callback_data="admin_manage_admins"))

    # Botones de utilidad
    markup.add(
        InlineKeyboardButton("👥 Ver Usuarios", callback_data="admin_view_users"),
        InlineKeyboardButton("📊 Estadísticas Detalladas", callback_data="admin_stats")
    )
    
    markup.add(InlineKeyboardButton("↩️ Volver al Menú Principal", callback_data="menu_back_main"))
    return markup


@bot.message_handler(func=lambda message: message.text == "👑 Panel Admin")
@bot.message_handler(commands=['admin_panel'])
def admin_panel(message):
    """Maneja el acceso al panel de administración."""
    try:
        user = message.from_user
        admin_data = get_admin_data(user.id)
        
        # 1. Verificar si es el Admin Supremo ID hardcodeado
        is_supremo = user.id == ADMIN_SUPREMO_ID

        # 2. Si no es admin y no es el Admin Supremo ID, denegar acceso
        if not admin_data and not is_supremo:
            bot.reply_to(message, get_message('error_no_permission', user.id), reply_markup=ReplyKeyboardRemove())
            return
            
        # 3. Determinar nivel y jurisdicción para el mensaje
        if is_supremo:
            # Asegurarse que el usuario tenga los datos completos (esto ya lo hace init_db)
            nivel = "supremo"
            region = "Global"
        elif admin_data:
            nivel = admin_data['nivel']
            # Se omite la obtención de la región por simplicidad, usando solo el nivel
            region = f"Nivel: {nivel.title()}"
        else:
            # Caso que no debería ocurrir si init_db funciona bien
            bot.reply_to(message, get_message('error_no_permission', user.id))
            return

        # Obtener estadísticas (Lógica mantenida de la versión anterior)
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado = 'activo'")
            usuarios_activos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM solicitudes")
            total_solicitudes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE estado = 'activa'")
            solicitudes_activas = cursor.fetchone()[0]
            
        admin_text = get_message('admin_panel_welcome', user.id) + f"""
*Tu Nivel:* {nivel.title()}
*Tu Jurisdicción:* {region}

📊 *Estadísticas:*\n- Usuarios: {total_usuarios}\n- Solicitudes Activas: {solicitudes_activas}
"""
        
        markup = get_admin_main_menu_keyboard(nivel)
        
        bot.send_message(message.chat.id, admin_text, reply_markup=markup, parse_mode='Markdown')
        log_audit("admin_panel_accessed", user.id)
        
        # Limpiar estado FSM
        if user.id in user_states:
            del user_states[user.id]

    except Exception as e:
        logger.error(f"Error en panel admin: {e}")
        bot.reply_to(message, "❌ Error al cargar el panel de administración.")
# ... (Código anterior - Parte 1) ...

# --- HANDLERS DE INTERACCIÓN DEL MENÚ DE ADMIN ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_menu_callbacks(call):
    """Maneja los callbacks del menú principal de administración."""
    user = call.from_user
    chat_id = call.message.chat.id
    action = call.data
    
    # 1. Verificar si el usuario es administrador
    admin_data = get_admin_data(user.id)
    is_supremo = user.id == ADMIN_SUPREMO_ID
    
    if not admin_data and not is_supremo:
        bot.answer_callback_query(call.id, get_message('error_no_permission', user.id))
        return

    # 2. Manejar la acción
    try:
        if action == 'admin_create_country':
            # Solo Supremo/Supremo 2
            if not is_supremo and admin_data['nivel'] not in ('supremo', 'supremo_2'):
                bot.answer_callback_query(call.id, "❌ No tienes permiso para crear países.", show_alert=True)
                return

            # Iniciar el FSM para crear País
            user_states[user.id] = {'step': ADMIN_FSM['crear_pais_nombre'], 'data': {}}
            bot.edit_message_text(
                "🌍 *Paso 1/2: Nombre del País*\n\nPor favor, ingresa el nombre completo del nuevo país (ej: Colombia).",
                chat_id,
                call.message.message_id,
                parse_mode='Markdown'
            )
            
        elif action == 'admin_create_provincia':
            # Solo Supremo/Supremo 2/País
            if not is_supremo and admin_data['nivel'] not in ('supremo', 'supremo_2', 'pais'):
                bot.answer_callback_query(call.id, "❌ No tienes permiso para crear provincias.", show_alert=True)
                return

            # Mostrar lista de países gestionables o de todos (si es supremo)
            countries = geography_db.get_admin_creatable_countries(user.id)
            if not countries:
                bot.answer_callback_query(call.id, "❌ No hay países creados o gestionables.", show_alert=True)
                return
                
            # Iniciar el FSM para seleccionar País de la Provincia
            user_states[user.id] = {'step': ADMIN_FSM['crear_prov_select_pais'], 'data': {}}
            markup = get_country_selection_keyboard(countries, prefix="admin_prov_")
            
            bot.edit_message_text(
                "📍 *Paso 1/2: País de la Provincia*\n\nSelecciona el país al que pertenece la nueva provincia:",
                chat_id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
        elif action == 'admin_create_zona':
            # Solo Supremo/Supremo 2/País/Provincia
            if not is_supremo and admin_data['nivel'] not in ('supremo', 'supremo_2', 'pais', 'provincia'):
                bot.answer_callback_query(call.id, "❌ No tienes permiso para crear zonas.", show_alert=True)
                return

            # Mostrar lista de provincias gestionables
            provincias = geography_db.get_admin_creatable_provincias(user.id)
            if not provincias:
                bot.answer_callback_query(call.id, "❌ No hay provincias creadas o gestionables.", show_alert=True)
                return
                
            # Iniciar el FSM para seleccionar Provincia de la Zona
            user_states[user.id] = {'step': ADMIN_FSM['crear_zona_select_prov'], 'data': {}}
            markup = get_provincia_selection_keyboard(provincias, prefix="admin_zona_")
            
            bot.edit_message_text(
                "🗺️ *Paso 1/2: Provincia de la Zona*\n\nSelecciona la provincia a la que pertenece la nueva zona/municipio:",
                chat_id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )

        elif action == 'admin_manage_admins':
             # Manejar la designación de admins
             user_states[user.id] = {'step': ADMIN_FSM['designar_admin_id'], 'data': {}}
             bot.edit_message_text(
                 "👑 *Gestión de Administradores*\n\nPor favor, *envíame el ID de Telegram* del usuario al que deseas designar o modificar su rol de administrador.",
                 chat_id,
                 call.message.message_id,
                 parse_mode='Markdown'
             )
        
        elif action == 'menu_back_admin':
            # Volver al menú principal del administrador
            admin_panel(call.message)
            
        else:
             bot.answer_callback_query(call.id)

    except Exception as e:
        logger.error(f"Error en handle_admin_menu_callbacks: {e}")
        bot.answer_callback_query(call.id, "❌ Error interno. Intenta /admin_panel de nuevo.")


# --- Funciones Helper para Teclados de Administración ---

def get_country_selection_keyboard(countries, prefix):
    """Genera teclado de selección de países para los flujos de administración."""
    markup = InlineKeyboardMarkup(row_width=2)
    for country in countries:
        markup.add(InlineKeyboardButton(country['nombre'], callback_data=f"{prefix}{country['id']}"))
    
    markup.add(InlineKeyboardButton("❌ Cancelar", callback_data="menu_back_admin"))
    return markup
    
def get_provincia_selection_keyboard(provincias, prefix):
    """Genera teclado de selección de provincias para los flujos de administración."""
    markup = InlineKeyboardMarkup(row_width=2)
    # Se agrupan por país para mejor visualización (solo si se necesita)
    
    for provincia in provincias:
        # Se muestra el nombre del país para contexto si el admin gestiona varios
        nombre_display = f"[{geography_db.get_geographic_level_name('pai', provincia['pais_id'])}] {provincia['nombre']}"
        markup.add(InlineKeyboardButton(nombre_display, callback_data=f"{prefix}{provincia['id']}"))
        
    markup.add(InlineKeyboardButton("❌ Cancelar", callback_data="menu_back_admin"))
    return markup
# ... (Código anterior - Parte 1 y Parte 2) ...

# --- HANDLER DE TEXTO PARA FLUJOS FSM DE ADMIN ---

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id]['step'].startswith('admin_crear_'))
def handle_admin_creation_text(message):
    """Maneja las entradas de texto para los flujos de creación geográfica (País, Provincia, Zona)."""
    user = message.from_user
    chat_id = message.chat.id
    user_data = user_states[user.id]
    step = user_data['step']
    text = message.text.strip()
    
    # 1. Crear País: Nombre (Paso 1)
    if step == ADMIN_FSM['crear_pais_nombre']:
        if not text:
            bot.reply_to(message, "❌ El nombre del país no puede estar vacío. Inténtalo de nuevo.")
            return

        user_data['data']['country_name'] = text
        user_data['step'] = ADMIN_FSM['crear_pais_codigo']
        
        bot.send_message(
            chat_id, 
            "🌍 *Paso 2/2: Código del País*\n\nIngresa un código corto de 3 letras para este país (ej: CUB, COL, MEX). Este será el identificador interno.",
            parse_mode='Markdown'
        )
    
    # 2. Crear País: Código (Paso 2 y Final)
    elif step == ADMIN_FSM['crear_pais_codigo']:
        if not text or len(text) != 3 or not text.isalpha():
            bot.reply_to(message, "❌ El código debe ser de exactamente 3 letras. Inténtalo de nuevo.")
            return
            
        country_name = user_data['data']['country_name']
        country_code = text.upper()
        
        result, new_id = geography_db.create_country(user.id, country_name, country_code)
        
        if result == "success":
            bot.send_message(
                chat_id, 
                f"✅ *País Creado:* {country_name} ({country_code}). ID: #{new_id}",
                parse_mode='Markdown',
                reply_markup=get_admin_main_menu_keyboard(get_admin_data(user.id)['nivel'] if get_admin_data(user.id) else 'supremo')
            )
            log_audit("country_created", user.id, f"País: {country_name}, Código: {country_code}")
            del user_states[user.id]
        elif result == "error_already_exists":
             bot.send_message(chat_id, f"❌ Ya existe un país con ese nombre o código ({country_code}). Intenta de nuevo con otro código.")
        else:
             bot.send_message(chat_id, f"❌ Error al guardar el país en la DB: {result}")
             del user_states[user.id]
             
    # 3. Crear Provincia: Nombre (Paso 2 y Final)
    elif step == ADMIN_FSM['crear_prov_nombre']:
        if not text:
            bot.reply_to(message, "❌ El nombre de la provincia no puede estar vacío. Inténtalo de nuevo.")
            return

        pais_id = user_data['data']['pais_id']
        provincia_name = text
        
        result, new_id = geography_db.create_provincia(user.id, pais_id, provincia_name)
        
        if result == "success":
            pais_name = geography_db.get_geographic_level_name('pai', pais_id)
            bot.send_message(
                chat_id, 
                f"✅ *Provincia Creada:* {provincia_name} en {pais_name}. ID: #{new_id}",
                parse_mode='Markdown',
                reply_markup=get_admin_main_menu_keyboard(get_admin_data(user.id)['nivel'] if get_admin_data(user.id) else 'supremo')
            )
            log_audit("provincia_created", user.id, f"Provincia: {provincia_name}, País ID: {pais_id}")
            del user_states[user.id]
        elif result == "error_already_exists":
             bot.send_message(chat_id, f"❌ Ya existe una provincia con ese nombre en este país.")
        else:
             bot.send_message(chat_id, f"❌ Error al guardar la provincia en la DB: {result}")
             del user_states[user.id]
             
    # 4. Crear Zona: Nombre (Paso 2 y Final)
    elif step == ADMIN_FSM['crear_zona_nombre']:
        if not text:
            bot.reply_to(message, "❌ El nombre de la zona no puede estar vacío. Inténtalo de nuevo.")
            return

        provincia_id = user_data['data']['provincia_id']
        zona_name = text
        
        result, new_id = geography_db.create_zona(user.id, provincia_id, zona_name)
        
        if result == "success":
            provincia_name = geography_db.get_geographic_level_name('provinci', provincia_id)
            bot.send_message(
                chat_id, 
                f"✅ *Zona Creada:* {zona_name} en {provincia_name}. ID: #{new_id}",
                parse_mode='Markdown',
                reply_markup=get_admin_main_menu_keyboard(get_admin_data(user.id)['nivel'] if get_admin_data(user.id) else 'supremo')
            )
            log_audit("zona_created", user.id, f"Zona: {zona_name}, Provincia ID: {provincia_id}")
            del user_states[user.id]
        elif result == "error_already_exists":
             bot.send_message(chat_id, f"❌ Ya existe una zona con ese nombre en esta provincia.")
        else:
             bot.send_message(chat_id, f"❌ Error al guardar la zona en la DB: {result}")
             del user_states[user.id]
    
    else:
        # En caso de que se pierda el paso
        bot.send_message(chat_id, "❌ Error de estado FSM. Volviendo al panel...", reply_markup=get_admin_main_menu_keyboard(get_admin_data(user.id)['nivel'] if get_admin_data(user.id) else 'supremo'))
        if user.id in user_states:
            del user_states[user.id]


# --- HANDLERS DE CALLBACKS DE SELECCIÓN GEOGRÁFICA ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_prov_') or call.data.startswith('admin_zona_'))
def handle_admin_selection_callbacks(call):
    """Maneja la selección de país o provincia en los flujos de creación."""
    user = call.from_user
    chat_id = call.message.chat.id
    user_data = user_states.get(user.id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Proceso expirado. Intenta de nuevo desde el Panel Admin.")
        return

    # 1. Selección de País para la Provincia (admin_prov_PAIS_ID)
    if call.data.startswith('admin_prov_') and user_data['step'] == ADMIN_FSM['crear_prov_select_pais']:
        pais_id = int(call.data.split('_')[2])
        pais_name = geography_db.get_geographic_level_name('pai', pais_id)
        
        user_data['data']['pais_id'] = pais_id
        user_data['step'] = ADMIN_FSM['crear_prov_nombre']
        
        bot.edit_message_text(
            f"📍 *Paso 2/2: Nombre de la Provincia*\n\nPaís seleccionado: **{pais_name}**.\n\nAhora, ingresa el nombre de la nueva provincia/estado.",
            chat_id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        
    # 2. Selección de Provincia para la Zona (admin_zona_PROVINCIA_ID)
    elif call.data.startswith('admin_zona_') and user_data['step'] == ADMIN_FSM['crear_zona_select_prov']:
        provincia_id = int(call.data.split('_')[2])
        provincia_name = geography_db.get_geographic_level_name('provinci', provincia_id)
        
        user_data['data']['provincia_id'] = provincia_id
        user_data['step'] = ADMIN_FSM['crear_zona_nombre']
        
        bot.edit_message_text(
            f"🗺️ *Paso 2/2: Nombre de la Zona*\n\nProvincia seleccionada: **{provincia_name}**.\n\nAhora, ingresa el nombre de la nueva zona/municipio.",
            chat_id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
    
    else:
        bot.answer_callback_query(call.id, "❌ Error de selección o paso incorrecto.")

# ... (Código anterior - Partes 1, 2 y 3) ...

# --- HANDLER DE TEXTO PARA FLUJOS FSM DE DESIGNACIÓN DE ADMIN ---

@bot.message_handler(func=lambda message: message.from_user.id in user_states and user_states[message.from_user.id]['step'] == ADMIN_FSM['designar_admin_id'])
def handle_admin_designation_id_input(message):
    """Paso 1: Recibir el ID de Telegram del usuario a designar."""
    user = message.from_user
    chat_id = message.chat.id
    user_data = user_states.get(user.id)
    
    if not user_data:
        bot.reply_to(message, "❌ El proceso expiró. Intenta de nuevo desde el Panel Admin.")
        return

    try:
        # Asegurar que el texto sea un número de Telegram ID
        target_telegram_id = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ Por favor, ingresa un ID de Telegram válido (solo números).")
        return

    # 1. Verificar que no se esté designando a sí mismo
    if target_telegram_id == user.id:
        bot.reply_to(message, "❌ No puedes designarte o modificar tu propio rol por este medio.")
        del user_states[user.id]
        return

    # 2. Verificar que el usuario exista en la BD
    target_user_db = get_user_by_telegram_id(target_telegram_id)
    if not target_user_db:
        bot.reply_to(message, f"❌ El usuario con ID `{target_telegram_id}` no está registrado en la base de datos de EcoTransportistas. Pídele que use /start.")
        del user_states[user.id]
        return

    # 3. Almacenar el ID del usuario interno (ID de la tabla usuarios)
    user_data['data']['target_telegram_id'] = target_telegram_id
    user_data['data']['target_user_internal_id'] = target_user_db['id']
    user_data['step'] = ADMIN_FSM['designar_admin_select_level']

    # 4. Mostrar opciones de nivel
    markup = get_admin_level_selection_keyboard()
    
    bot.send_message(
        chat_id, 
        f"👑 *Paso 2/3: Seleccionar Nivel*\n\nUsuario a designar: `{target_telegram_id}` ({target_user_db['nombre_completo']})\n\nSelecciona el nivel de administración que deseas asignar:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# --- Funciones Helper para Teclados de Designación ---

def get_admin_level_selection_keyboard():
    """Teclado para seleccionar el nivel de administración."""
    markup = InlineKeyboardMarkup(row_width=2)
    
    levels = [
        ("👑 Admin Supremo 2", "supremo_2"),
        ("🌍 Admin de País", "pais"),
        ("📍 Admin de Provincia", "provincia"),
        ("🗺️ Admin de Zona", "zona"),
    ]
    
    for text, level in levels:
        markup.add(InlineKeyboardButton(text, callback_data=f"admin_level_{level}"))
        
    markup.add(InlineKeyboardButton("❌ Cancelar Designación", callback_data="menu_back_admin"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_level_'))
def handle_admin_level_selection(call):
    """Paso 2: Seleccionar el nivel de administración (País, Provincia, Zona)."""
    user = call.from_user
    chat_id = call.message.chat.id
    user_data = user_states.get(user.id)
    
    if not user_data or user_data['step'] != ADMIN_FSM['designar_admin_select_level']:
        bot.answer_callback_query(call.id, "❌ Proceso expirado o incorrecto.")
        return

    nivel = call.data.split('_')[2]
    user_data['data']['admin_level'] = nivel
    
    # 1. Determinar el siguiente paso (Selección de Región o Finalizar)
    if nivel == 'supremo_2':
        # Admin Supremo 2: No necesita región, se asigna directamente
        call.data = f"admin_region_finalize" # Forzar la llamada al siguiente handler para finalizar
        handle_admin_region_selection(call)
        return
        
    elif nivel == 'pais':
        # Admin de País: Debe seleccionar un país
        countries = geography_db.get_admin_creatable_countries(user.id)
        if not countries:
            bot.answer_callback_query(call.id, "❌ No hay países disponibles para asignar.", show_alert=True)
            return

        user_data['step'] = ADMIN_FSM['designar_admin_select_region']
        markup = get_admin_region_selection_keyboard(countries, "country")
        
        bot.edit_message_text(
            f"🌍 *Paso 3/3: Seleccionar Región (País)*\n\nNivel: *{nivel.title()}*.\nSelecciona el **País** que gestionará este administrador:",
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    elif nivel == 'provincia':
        # Admin de Provincia: Debe seleccionar una provincia
        provincias = geography_db.get_admin_creatable_provincias(user.id)
        if not provincias:
            bot.answer_callback_query(call.id, "❌ No hay provincias disponibles para asignar.", show_alert=True)
            return

        user_data['step'] = ADMIN_FSM['designar_admin_select_region']
        markup = get_admin_region_selection_keyboard(provincias, "provincia")
        
        bot.edit_message_text(
            f"📍 *Paso 3/3: Seleccionar Región (Provincia)*\n\nNivel: *{nivel.title()}*.\nSelecciona la **Provincia** que gestionará este administrador:",
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )

    elif nivel == 'zona':
        # Admin de Zona: Requiere selección anidada (País -> Provincia -> Zona)
        countries = geography_db.get_admin_creatable_countries(user.id)
        if not countries:
            bot.answer_callback_query(call.id, "❌ No hay países para iniciar la selección de Zona.", show_alert=True)
            return

        user_data['step'] = ADMIN_FSM['designar_admin_select_region']
        markup = get_admin_region_selection_keyboard(countries, "zone_country_select")
        
        bot.edit_message_text(
            f"🗺️ *Paso 3/3: Seleccionar Región (Zona - Paso 1/2)*\n\nNivel: *{nivel.title()}*.\nSelecciona el **País** para encontrar la Zona que gestionará:",
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    bot.answer_callback_query(call.id)


def get_admin_region_selection_keyboard(regions, type_, back_data=None):
    """Genera teclado de selección de región (País, Provincia, o primer paso de Zona)."""
    markup = InlineKeyboardMarkup(row_width=2)
    
    if type_ == "country":
        for region in regions:
            # admin_region_country_ID
            markup.add(InlineKeyboardButton(region['nombre'], callback_data=f"admin_region_country_{region['id']}"))
    
    elif type_ == "provincia":
         for region in regions:
             # Nota: Se asume que las regiones de 'provincia' tienen 'pais_id'
             pais_name = geography_db.get_geographic_level_name('pai', region['pais_id'])
             markup.add(InlineKeyboardButton(f"[{pais_name}] {region['nombre']}", callback_data=f"admin_region_provincia_{region['id']}"))

    elif type_ == "zone_country_select":
        # Se usa este tipo como paso inicial para Zona: lleva a la selección de provincia
        for region in regions:
            # admin_region_zone_country_ID (No asigna, solo navega)
            markup.add(InlineKeyboardButton(region['nombre'], callback_data=f"admin_region_zone_country_{region['id']}"))
            
    elif type_ == "zone_prov_select":
        # Se usa este tipo para la selección de provincia en el flujo de zona: lleva a la selección de zona
        for region in regions:
            pais_name = geography_db.get_geographic_level_name('pai', region['pais_id'])
            # admin_region_zone_provincia_ID (No asigna, solo navega)
            markup.add(InlineKeyboardButton(f"[{pais_name}] {region['nombre']}", callback_data=f"admin_region_zone_provincia_{region['id']}"))
            
    elif type_ == "zone_select":
        # Selección final de zona
        for region in regions:
            # admin_region_zona_ID (Asigna)
            markup.add(InlineKeyboardButton(region['nombre'], callback_data=f"admin_region_zona_{region['id']}"))

    # Botón de Cancelar
    markup.add(InlineKeyboardButton("❌ Cancelar Designación", callback_data="menu_back_admin"))
    return markup
# ... (Código anterior - Partes 1, 2, 3 y 4) ...

# --- HANDLER DE CALLBACKS DE SELECCIÓN DE REGIÓN ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_region_'))
def handle_admin_region_selection(call):
    """Paso 3: Seleccionar la región específica para el admin (País, Provincia, Zona)."""
    user = call.from_user
    chat_id = call.message.chat.id
    user_data = user_states.get(user.id)
    
    if not user_data or user_data['step'] != ADMIN_FSM['designar_admin_select_region'] and call.data != "admin_region_finalize":
        bot.answer_callback_query(call.id, "❌ Proceso expirado o incorrecto.")
        return

    admin_level = user_data['data']['admin_level']
    target_user_internal_id = user_data['data']['target_user_internal_id']
    target_telegram_id = user_data['data']['target_telegram_id']
    
    # 1. FINALIZAR ASIGNACIÓN (Para Admin Supremo 2 y la selección final de región)
    if call.data == "admin_region_finalize" or call.data.startswith('admin_region_country_') or call.data.startswith('admin_region_provincia_') or call.data.startswith('admin_region_zona_'):
        
        region_id = None
        region_name = "Global"

        # Capturar la región seleccionada para País, Provincia o Zona
        if call.data.startswith('admin_region_country_'):
            region_id = int(call.data.split('_')[3])
            region_name = geography_db.get_geographic_level_name('pai', region_id)
        elif call.data.startswith('admin_region_provincia_'):
            region_id = int(call.data.split('_')[3])
            region_name = geography_db.get_geographic_level_name('provinci', region_id)
        elif call.data.startswith('admin_region_zona_'):
            region_id = int(call.data.split('_')[3])
            zone_data = geography_db.get_zone_data(region_id)
            if zone_data:
                region_name = f"{zone_data['pais_nombre']}/{zone_data['provincia_nombre']}/{zone_data['zona_nombre']}"

        # Asignación final en la DB
        success = set_admin_role(target_user_internal_id, admin_level, region_id)
        
        if success:
            bot.edit_message_text(
                f"✅ *ADMINISTRADOR DESIGNADO*\n\nUsuario: `{target_telegram_id}`\nNivel: *{admin_level.title()}*\nRegión: *{region_name}*",
                chat_id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=get_admin_main_menu_keyboard(get_admin_data(user.id)['nivel'] if get_admin_data(user.id) else 'supremo')
            )
            log_audit("admin_role_assigned", user.id, f"Target: {target_telegram_id}, Nivel: {admin_level}, Región ID: {region_id}")
        else:
            bot.edit_message_text(
                f"❌ Error crítico al guardar el rol de administrador en la base de datos.",
                chat_id,
                call.message.message_id,
                reply_markup=get_admin_main_menu_keyboard(get_admin_data(user.id)['nivel'] if get_admin_data(user.id) else 'supremo')
            )
            
        del user_states[user.id]
        bot.answer_callback_query(call.id)
        return

    # 2. NAVEGACIÓN ZONA: Selección de Provincia (admin_region_zone_country_ID)
    elif call.data.startswith('admin_region_zone_country_'):
        country_id = int(call.data.split('_')[4])
        provincias = geography_db.get_admin_creatable_provincias(user.id)
        # Filtrar provincias que pertenecen al país seleccionado
        provincias_filtradas = [p for p in provincias if p['pais_id'] == country_id]
        
        if not provincias_filtradas:
            bot.answer_callback_query(call.id, "❌ No hay provincias para seleccionar Zona en este país.", show_alert=True)
            return
            
        markup = get_admin_region_selection_keyboard(provincias_filtradas, "zone_prov_select", back_data="admin_level_zona")
        
        bot.edit_message_text(
            f"🗺️ *Paso 3/3: Seleccionar Región (Zona - Paso 2/2)*\n\nNivel: *{admin_level.title()}*.\nSelecciona la **Provincia** para encontrar la Zona:",
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)

    # 3. NAVEGACIÓN ZONA: Selección de Zona (admin_region_zone_provincia_ID)
    elif call.data.startswith('admin_region_zone_provincia_'):
        provincia_id = int(call.data.split('_')[4])
        zonas = geography_db.get_admin_creatable_zonas(user.id, provincia_id=provincia_id)
        
        if not zonas:
            bot.answer_callback_query(call.id, "❌ No hay zonas para seleccionar en esta provincia.", show_alert=True)
            return

        markup = get_admin_region_selection_keyboard(zonas, "zone_select", back_data=f"admin_region_zone_country_{zonas[0]['pais_id']}")
        
        bot.edit_message_text(
            f"🗺️ *Paso 3/3: Seleccionar Región (Zona - Paso Final)*\n\nNivel: *{admin_level.title()}*.\nSelecciona la **Zona** que gestionará:",
            chat_id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)

    else:
        bot.answer_callback_query(call.id, "❌ Opción no reconocida.")


def set_admin_role(user_internal_id, nivel, region_id):
    """Asigna o modifica un rol de administrador en la tabla administradores."""
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # 1. Desactivar roles anteriores (si existen)
            cursor.execute("UPDATE administradores SET estado = 'inactivo' WHERE usuario_id = ?", (user_internal_id,))
            
            # 2. Verificar si ya existe un registro inactivo para actualizar o insertar
            cursor.execute("SELECT id FROM administradores WHERE usuario_id = ?", (user_internal_id,))
            existing_id = cursor.fetchone()
            
            # 3. Determinar qué campo de región usar
            region_column = None
            if nivel == 'pais':
                region_column = 'pais_id'
            elif nivel == 'provincia':
                region_column = 'provincia_id'
            elif nivel == 'zona':
                region_column = 'zona_id'
            
            if existing_id:
                # 4. Actualizar registro existente
                sql_update = f'''
                    UPDATE administradores 
                    SET nivel = ?, estado = 'activo', {region_column} = ? 
                    WHERE id = ?
                ''' if region_column else '''
                    UPDATE administradores 
                    SET nivel = ?, estado = 'activo', pais_id = NULL, provincia_id = NULL, zona_id = NULL
                    WHERE id = ?
                '''
                params = [nivel, region_id, existing_id[0]] if region_column else [nivel, existing_id[0]]
                cursor.execute(sql_update, params)
            else:
                # 5. Insertar nuevo registro
                columns = ['usuario_id', 'nivel', 'estado']
                placeholders = ['?', '?', '?']
                values = [user_internal_id, nivel, 'activo']
                
                if region_column:
                    columns.append(region_column)
                    placeholders.append('?')
                    values.append(region_id)
                
                sql_insert = f"INSERT INTO administradores ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(sql_insert, values)
                
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error asignando rol de admin a usuario {user_internal_id}: {e}")
        return False

# IMPORTANTE: Asegurarse de que el manejo de otros callbacks ('admin_view_users', 'admin_stats')
# no cause conflictos o se elimine la funcionalidad. Se asume que estos son de baja prioridad
# y se gestionarán en la próxima interacción si el usuario los pide. Por ahora se ignora.

