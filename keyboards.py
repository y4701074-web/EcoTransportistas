from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
# Se elimina la importación de PROVINCIAS_CUBA, ZONAS_POR_PROVINCIA
import geography_db # Nueva dependencia

# --- Teclados de Utilidad ---

def get_language_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    return markup

def get_phone_keyboard():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("📞 Compartir teléfono", request_contact=True))
    return markup

def get_user_type_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🚚 Transportista", callback_data="type_transportista"),
        InlineKeyboardButton("📦 Solicitante", callback_data="type_solicitante"),
        InlineKeyboardButton("🎯 Ambos", callback_data="type_ambos")
    )
    return markup

# --- Teclados Geográficos Dinámicos ---

def get_countries_registration_keyboard():
    """Muestra la lista de países activos para que el usuario elija su lugar de residencia."""
    countries = geography_db.get_available_countries_for_registration()
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Manejar el caso de que no haya países creados por el admin
    if not countries:
        markup.add(InlineKeyboardButton("❌ No hay países disponibles", callback_data="no_countries"))
        return markup
        
    for country in countries:
        # data: reg_country_ID
        markup.add(InlineKeyboardButton(country['nombre'], callback_data=f"reg_country_{country['id']}"))
        
    return markup

def get_provincias_registration_keyboard(country_id):
    """Muestra la lista de provincias de un país para el registro."""
    provincias = geography_db.get_provincias_by_pais_id(country_id)
    markup = InlineKeyboardMarkup(row_width=2)
    
    if not provincias:
        markup.add(InlineKeyboardButton("❌ No hay provincias creadas", callback_data="no_provincias"))

    for provincia in provincias:
        # data: reg_prov_ID
        markup.add(InlineKeyboardButton(provincia['nombre'], callback_data=f"reg_prov_{provincia['id']}"))
    
    markup.add(InlineKeyboardButton("⬅️ Atrás (Cambiar País)", callback_data="reg_back_country"))
    
    return markup

def get_zonas_registration_keyboard(provincia_id):
    """Muestra la lista de zonas de una provincia para el registro."""
    zonas = geography_db.get_zonas_by_provincia_id(provincia_id)
    markup = InlineKeyboardMarkup(row_width=2)
    
    if not zonas:
        markup.add(InlineKeyboardButton("❌ No hay zonas creadas", callback_data="no_zonas"))
        
    for zona in zonas:
        # data: reg_zona_ID
        markup.add(InlineKeyboardButton(zona['nombre'], callback_data=f"reg_zona_{zona['id']}"))
    
    markup.add(InlineKeyboardButton("⬅️ Atrás (Cambiar Provincia)", callback_data="reg_back_prov"))
    
    return markup
# ... (Código anterior - Parte 1) ...

# --- Teclado del Menú Principal (Solicitado por el usuario) ---

def get_main_menu_keyboard(user_type, is_admin=False):
    """Muestra el menú principal basado en el rol del usuario. Mantiene estructura Reply."""
    
    # Botonera Reply (botones grandes)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Fila 1:
    row1 = []
    # 1. Botón fijo: Mi Perfil (con opción de editar y eliminar)
    row1.append(KeyboardButton("👤 Mi Perfil"))
    
    # 2. Botón fijo: Mis Vehículos
    row1.append(KeyboardButton("🚗 Mis Vehículos"))
    
    # Fila 2:
    row2 = []
    
    # 3. Solicitantes: Nueva Solicitud
    if user_type in ['solicitante', 'ambos']:
        row2.append(KeyboardButton("📦 Nueva Solicitud"))
    
    # 4. Transportistas: Ver Solicitudes
    if user_type in ['transportista', 'ambos']:
        row2.append(KeyboardButton("🔎 Ver Solicitudes"))
    
    # Fila 3:
    row3 = []
    
    # 5. Transportistas: Mis Zonas (NUEVA FUNCIÓN: Filtros de Carga y Ubicación)
    if user_type in ['transportista', 'ambos']:
        # Se renombra de "Mis Zonas" a "Mis Zonas (Filtros)" para aclarar función
        row3.append(KeyboardButton("🗺️ Mis Zonas (Filtros)"))
        
    # 6. Admin Panel (Solo si tiene rol de admin)
    if is_admin:
        row3.append(KeyboardButton("👑 Panel Admin"))
        
    if row1:
        markup.add(*row1)
    if row2:
        markup.add(*row2)
    if row3:
        markup.add(*row3)
        
    return markup

# --- Teclados de Solicitudes (Mantenidos) ---

def get_vehicle_type_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    vehicles = [
        ("🏍️ Moto", "moto"),
        ("🚘 Auto", "auto"),
        ("🚐 Camioneta", "camioneta"),
        ("🚚 Camión", "camion"),
        ("🚛 Rastra", "rastra")
    ]
    for text, data in vehicles:
        markup.add(InlineKeyboardButton(text, callback_data=f"vehicle_{data}"))
    return markup

def get_cargo_type_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    cargo_types = [
        ("📦 Paquete Pequeño", "paquete_pequeno"),
        ("📱 Electrónicos", "electronicos"),
        ("🛋️ Muebles", "muebles"),
        ("🍎 Alimentos", "alimentos"),
        ("🏭 Materiales", "materiales"),
        ("🔧 Herramientas", "herramientas")
    ]
    for text, data in cargo_types:
        markup.add(InlineKeyboardButton(text, callback_data=f"cargo_{data}"))
    return markup

def get_request_confirmation_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Publicar", callback_data="publish_yes"),
        InlineKeyboardButton("❌ Cancelar", callback_data="publish_no")
    )
    return markup
# ... (Código anterior - Parte 1 y Parte 2) ...

def get_accept_request_keyboard(solicitud_id):
    """Teclado que ve el transportista para aceptar la solicitud."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Aceptar Solicitud", callback_data=f"accept_{solicitud_id}"))
    return markup

def get_solicitante_confirmation_keyboard(solicitud_id):
    """Teclado que ve el solicitante para confirmar o rechazar al transportista."""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirmar Transportista", callback_data=f"confirm_{solicitud_id}"),
        InlineKeyboardButton("❌ Rechazar y Re-publicar", callback_data=f"reject_{solicitud_id}")
    )
    return markup

# --- TECLADOS PARA GESTIÓN DE FILTROS DE TRABAJO (Mis Zonas) ---

def get_work_zones_menu(user_id):
    """Menú principal de la gestión de filtros del transportista."""
    
    # Obtener el ID interno del usuario
    user_db_id = geography_db.get_user_internal_id(user_id)
    if not user_db_id:
        return None
        
    # Obtener la información del usuario para el país de registro
    # (Se asume que los transportistas solo filtran dentro del país que seleccionaron en el registro)
    import db # Importación local
    user_data = db.get_user_by_telegram_id(user_id)
    pais_id = user_data['pais_id'] if user_data else None

    markup = InlineKeyboardMarkup(row_width=1)
    
    # 1. Configurar capacidad de carga
    markup.add(InlineKeyboardButton("⚖️ Configurar Carga Máxima (Toneladas)", callback_data="filter_set_capacity"))
    
    # 2. Seleccionar Países (para filtrar las solicitudes)
    # Por ahora, solo se puede trabajar en los países creados, se omite el filtro de país del registro inicial
    countries = geography_db.get_available_countries_for_registration()
    
    # Se añade solo el botón para seleccionar Países/Provincias/Zonas
    if countries:
        markup.add(InlineKeyboardButton("🗺️ Seleccionar Países de Trabajo", callback_data="filter_select_country"))
    else:
        markup.add(InlineKeyboardButton("❌ No hay países para seleccionar zonas", callback_data="filter_no_zones"))
    
    markup.add(InlineKeyboardButton("↩️ Volver al Menú Principal", callback_data="menu_back_main"))
    return markup

def get_work_countries_keyboard(current_zone_ids):
    """Muestra la lista de países para la selección de zonas de trabajo."""
    countries = geography_db.get_available_countries_for_registration()
    markup = InlineKeyboardMarkup(row_width=2)
    
    if not countries:
        markup.add(InlineKeyboardButton("❌ No hay países disponibles", callback_data="filter_no_countries"))
        return markup

    for country in countries:
        # data: work_country_ID
        # No se usa un checkbox porque el filtro solo necesita llegar hasta el nivel de ZONA
        markup.add(InlineKeyboardButton(country['nombre'], callback_data=f"work_country_{country['id']}"))
        
    markup.add(InlineKeyboardButton("✅ Finalizar Selección", callback_data="filter_finish"))
    markup.add(InlineKeyboardButton("⬅️ Volver a Filtros", callback_data="filter_back_menu"))
    
    return markup
    
def get_work_provincias_keyboard(country_id, current_zone_ids):
    """Muestra las provincias de un país y las opciones de Todas/Atrás/Finalizar."""
    # Nota: No se requiere checkbox en provincias, solo sirve como navegación
    provincias = geography_db.get_provincias_by_pais_id(country_id, include_all_option=True) # Incluye "Todas las Provincias"
    markup = InlineKeyboardMarkup(row_width=2)
    
    if not provincias:
        markup.add(InlineKeyboardButton("❌ No hay provincias en este país", callback_data="filter_no_provincias"))
        markup.add(InlineKeyboardButton("⬅️ Volver a Países", callback_data="filter_select_country"))
        return markup
        
    for provincia in provincias:
        if provincia['id'] == 0:
            # Opción especial: "Todas las Provincias"
            # data: work_all_prov_PAIS_ID
            markup.add(InlineKeyboardButton(provincia['nombre'], callback_data=f"work_all_prov_{country_id}"), row_width=1)
        else:
            # data: work_prov_PROVINCIA_ID
            markup.add(InlineKeyboardButton(provincia['nombre'], callback_data=f"work_prov_{provincia['id']}"))
            
    markup.add(InlineKeyboardButton("✅ Finalizar Selección", callback_data="filter_finish"))
    markup.add(InlineKeyboardButton("⬅️ Volver a Países", callback_data="filter_select_country"))
    
    return markup

def get_work_zones_selection_keyboard(provincia_id, current_zone_ids):
    """Muestra las zonas de una provincia con checkbox para selección múltiple."""
    zonas = geography_db.get_zonas_by_provincia_id(provincia_id, include_all_option=True) # Incluye "Todas las Zonas"
    markup = InlineKeyboardMarkup(row_width=2)
    
    if not zonas:
        markup.add(InlineKeyboardButton("❌ No hay zonas en esta provincia", callback_data="filter_no_zones_prov"))
        markup.add(InlineKeyboardButton("⬅️ Volver a Provincias", callback_data=f"work_country_{geography_db.get_zone_data(provincia_id)['pais_id']}"))
        return markup
        
    for zona in zonas:
        is_selected = zona['id'] in current_zone_ids
        checkbox = "☑️" if is_selected else "🔲"
        
        if zona['id'] == 0:
            # Opción especial: "Todas las Zonas"
            # data: work_all_zone_PROVINCIA_ID
            markup.add(InlineKeyboardButton(f"{checkbox} {zona['nombre']}", callback_data=f"work_all_zone_{provincia_id}"), row_width=1)
        else:
            # data: work_zone_ZONA_ID
            markup.add(InlineKeyboardButton(f"{checkbox} {zona['nombre']}", callback_data=f"work_zone_{zona['id']}"))
            
    markup.add(InlineKeyboardButton("✅ Finalizar Selección", callback_data="filter_finish"))
    markup.add(InlineKeyboardButton("⬅️ Volver a Provincias", callback_data=f"work_back_prov_{provincia_id}"))

    return markup
