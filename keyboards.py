# keyboards.py
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
import geography_db
import db  # ✅ AÑADIR ESTA IMPORTACIÓN CRÍTICA

# ... (el resto del código de keyboards.py se mantiene igual, solo asegúrate de que existe la importación de 'db' arriba)

# En la función get_work_zones_menu, cambiar:
def get_work_zones_menu(user_id):
    """Menú principal de la gestión de filtros del transportista."""
    
    # Obtener el ID interno del usuario - ✅ CORREGIDO: usar db en lugar de geography_db
    user_db_id = db.get_user_internal_id(user_id)
    if not user_db_id:
        return None
        
    # Obtener la información del usuario para el país de registro
    user_data = db.get_user_by_telegram_id(user_id)
    pais_id = user_data['pais_id'] if user_data else None

    markup = InlineKeyboardMarkup(row_width=1)
    
    # 1. Configurar capacidad de carga
    markup.add(InlineKeyboardButton("⚖️ Configurar Carga Máxima (Toneladas)", callback_data="filter_set_capacity"))
    
    # 2. Seleccionar Países (para filtrar las solicitudes)
    countries = geography_db.get_available_countries_for_registration()
    
    # Se añade solo el botón para seleccionar Países/Provincias/Zonas
    if countries:
        markup.add(InlineKeyboardButton("🗺️ Seleccionar Países de Trabajo", callback_data="filter_select_country"))
    else:
        markup.add(InlineKeyboardButton("❌ No hay países para seleccionar zonas", callback_data="filter_no_zones"))
    
    markup.add(InlineKeyboardButton("↩️ Volver al Menú Principal", callback_data="menu_back_main"))
    return markup