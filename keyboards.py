from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from config import PROVINCIAS_CUBA, ZONAS_POR_PROVINCIA

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

def get_provincias_keyboard():
    markup = InlineKeyboardMarkup()
    for code, name in PROVINCIAS_CUBA.items():
        markup.add(InlineKeyboardButton(name, callback_data=f"prov_{code}"))
    return markup

def get_zonas_keyboard(provincia_code):
    markup = InlineKeyboardMarkup()
    zonas = ZONAS_POR_PROVINCIA.get(provincia_code, ['Zona Central'])
    
    for zona in zonas:
        markup.add(InlineKeyboardButton(zona, callback_data=f"zona_{zona}"))
    return markup

def get_main_menu_keyboard(user_type):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if user_type == 'transportista':
        buttons = ["📦 Ver Solicitudes", "🚚 Mis Vehículos", "📍 Mis Zonas", "👤 Mi Perfil"]
    elif user_type == 'solicitante':
        buttons = ["📦 Nueva Solicitud", "📋 Mis Solicitudes", "👤 Mi Perfil", "🆘 Ayuda"]
    else:  # ambos
        buttons = ["📦 Nueva Solicitud", "📦 Ver Solicitudes", "🚚 Mis Vehículos", "👤 Mi Perfil"]
    
    markup.add(*[KeyboardButton(btn) for btn in buttons])
    return markup

def get_vehicle_type_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    vehicles = [
        ("🚲 Bicicleta/Moto", "bicicleta_moto"),
        ("🚗 Auto/Taxi", "auto_taxi"),
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

def get_accept_request_keyboard(solicitud_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Aceptar Solicitud", callback_data=f"accept_{solicitud_id}"))
    return markup

def get_solicitante_confirmation_keyboard(solicitud_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_{solicitud_id}"),
        InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{solicitud_id}")
    )
    return markup
      
