import os
import logging
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN INICIAL Y LOGGING ---

# Cargar variables de entorno del archivo .env (si existe)
load_dotenv()

# Configuración básica de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("✅ Iniciando configuración del bot.") 

# -------------------------------------------------------------
# --- 2. VARIABLES DE ENTORNO CRÍTICAS (DEBEN ESTAR DEFINIDAS) ---
# -------------------------------------------------------------

# BOT_TOKEN es esencial y su ausencia detiene el inicio.
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ ERROR: La variable de entorno 'BOT_TOKEN' no está definida.")
    raise SystemExit("BOT_TOKEN environment variable is required to start the bot.")

# ID del Administrador Supremo: Se carga, se valida como entero.
ADMIN_SUPREMO_ID_DEFAULT = '6288842089'  # ID de ejemplo
ADMIN_SUPREMO_ID_STR = os.getenv('ADMIN_SUPREMO_ID', ADMIN_SUPREMO_ID_DEFAULT)

try:
    ADMIN_SUPREMO_ID = int(ADMIN_SUPREMO_ID_STR)
except ValueError:
    logger.error(f"❌ ERROR: 'ADMIN_SUPREMO_ID' ('{ADMIN_SUPREMO_ID_STR}') debe ser un número entero.")
    raise SystemExit("ADMIN_SUPREMO_ID must be an integer.")

# Nombre del Administrador Supremo.
ADMIN_SUPREMO = os.getenv('ADMIN_SUPREMO', 'Admin Supremo')


# ---------------------------------------------------
# --- 3. CONSTANTES DE ESTADO, ROL Y CATEGORÍA (FSM) ---
# ---------------------------------------------------

## Estados del Proceso de Registro (FSM States)
# 🚨 CORRECCIÓN: Renombradas a STATE_... para coincidir con la importación en registro.py
STATE_WAITING_LANGUAGE = 'waiting_language'
STATE_WAITING_NAME = 'waiting_name'
STATE_WAITING_PHONE = 'waiting_phone' 
STATE_WAITING_ROLE = 'waiting_role'
STATE_WAITING_PROVINCIA = 'waiting_provincia'
STATE_WAITING_ZONAS = 'waiting_zonas'
STATE_ACTIVE = 'active'
STATE_BANNED = 'banned'

## Roles de Usuario
ROLE_PENDIENTE = 'pendiente'
ROLE_SOLICITANTE = 'solicitante'
ROLE_TRANSPORTISTA = 'transportista'
ROLE_AMBOS = 'ambos'

## Constantes de Categorías
CATEGORIES = {
    'CARGO_TYPES': [ # Tipos de carga
        'Paquete pequeño', 
        'Caja mediana', 
        'Mueble grande', 
        'Material de construcción', 
        'Especial/Otro'
    ],
    'VEHICLE_TYPES': [ # Tipos de vehículo
        'Moto/Bicicleta', 
        'Auto/Camioneta', 
        'Camión pequeño (hasta 2T)', 
        'Camión grande (más de 2T)'
    ]
}


# ----------------------------------------------
# --- 4. DICCIONARIOS MULTIIDIOMA (MESSAGES) ---
# ----------------------------------------------

MESSAGES = {
    'es': {
        'welcome': "🚀 *¡Bienvenido a EcoTransportistas!* 🌟\n\n👋 Hola {name}!\n\n🌍 *¿Qué es EcoTransportistas?*\nEs tu plataforma para conectar *transportistas* con *personas que necesitan enviar cosas*.\n\n📦 *¿Eres Solicitante?* → Encuentra transporte rápido y confiable\n🚚 *¿Eres Transportista?* → Consigue más clientes en tu zona\n\n🛠️ *¿Cómo empezar?*\n1️⃣ Usa /registro para crear tu perfil\n2️⃣ Elige tu tipo de usuario\n3️⃣ ¡Comienza a conectar!",
        'choose_language': "🌍 *Selecciona tu idioma / Choose your language:*",
        'registration_start': "📝 *Iniciando registro...*\n\nPor favor comparte tu número de teléfono para verificar tu identidad:",
        'phone_received': "✅ Teléfono recibido. Ahora, ¿cuál es tu nombre completo?",
        'name_received': "👤 Nombre recibido. Ahora, ¿qué rol(es) vas a desempeñar?",
        'user_type_selected': "Tipo de usuario seleccionado. Por favor, **selecciona el país** donde resides (o donde más trabajas) para continuar:",
        'country_selected_continue': "✅ País seleccionado: {pais}. Ahora, por favor, **selecciona la provincia**.",
        'profile_complete': "🎉 *¡Registro Completo!* 🎉\n\n**Resumen de tu Perfil:**\n- 👤 Nombre: {name}\n- 📞 Teléfono: {phone}\n- 🗺️ País: {pais}\n- 🗺️ Provincia: {provincia}\n- 🚚 Rol: {tipo}\n\n¡Usa el menú para empezar!",
        'admin_panel_welcome': "👑 *Panel de Administración Supremo* 👑\n\n¿Qué deseas gestionar?",

        # Mensajes de error
        'error_no_permission': "❌ *Acceso denegado*. No tienes permisos para esta acción.",
        'error_not_registered': "❌ No estás registrado. Usa /start o /registro para empezar.",

        # Menús y Perfil
        'main_menu': "⚙️ *Menú Principal*\n\nSelecciona la acción que deseas realizar:",
        'my_profile_info': "👤 *Tu Perfil*\n\n- Nombre: {name}\n- Teléfono: {phone}\n- Rol: {tipo}\n- País: {pais}\n- Provincia: {provincia}\n- Estado: {estado}\n\n*Información de Transportista:*\n- Carga Máxima: {capacidad}\n- Vehículos: {vehiculos}\n- Zonas de Trabajo: {zonas_trabajo}",

        # Solicitudes
        'request_vehicle_type': "🚗 ¿Qué tipo de vehículo necesitas para el transporte?",
        'request_cargo_type': "📦 ¿Cuál es el tipo de carga?",
        'request_description': "📝 Por favor, proporciona una breve descripción de la carga (ej: 2 cajas, 1 cama matrimonial, etc.)",
        'request_pickup_address': "📍 Ahora, la **dirección exacta de recogida** (con puntos de referencia opcionales):",
        'request_delivery_address': "🎯 Ahora, la **dirección exacta de entrega** (con puntos de referencia opcionales):",
        'request_budget': "💰 ¿Cuál es tu presupuesto estimado para este transporte (ej: 500 CUP)?",
        'request_review': "🔍 *Revisa tu Solicitud*\n\n🚚 Vehículo: {vehicle}\n📦 Carga: {cargo}\n📝 Descripción: {description}\n📍 Recogida: {pickup}\n🎯 Entrega: {delivery}\n💰 Presupuesto: {budget:.2f} CUP\n\n¿Publicar ahora?",
        'request_published': "✅ *Solicitud Publicada*. Notificando transportistas en tu zona...",
        'error_not_solicitante': "❌ Solo los usuarios *Solicitantes* o *Ambos* pueden crear solicitudes.",
        'error_not_transportista': "❌ Solo los usuarios *Transportistas* o *Ambos* pueden ver solicitudes.",
        'no_requests_found': "😔 No se encontraron solicitudes activas en tus zonas de trabajo con tu filtro de carga.",

        # Interacciones
        'request_accepted': "✅ *Solicitud aceptada*. El solicitante ha sido notificado para la confirmación.",
        'request_not_available': "❌ Esta solicitud ya no está disponible (fue tomada o procesada).",
        'request_expired': "⏰ *La solicitud #{id} ha expirado*\\n\\nEl tiempo de confirmación terminó. La solicitud está disponible de nuevo.",
        'confirmation_sent': "✅ Solicitud aceptada. Esperando la confirmación del solicitante...",
        'request_processed': "❌ Esta solicitud ya ha sido procesada",
        'request_confirmed_solicitante': "✅ *Solicitud confirmada con éxito!*\\n\\nEl transportista ha sido notificado y se pondrá en contacto contigo pronto.",
        'request_rejected': "❌ *Rechazado*. El solicitante ha rechazado la asignación. La solicitud está activa de nuevo.",
    },
    'en': {
        # ... (Agregar mensajes en inglés aquí)
    }
}
