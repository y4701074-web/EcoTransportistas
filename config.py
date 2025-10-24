import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env (si existe)
load_dotenv()

# Configuración logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("✅ Instancia del bot creada.") 

# Configuración - VARIABLES DE ENTORNO CRÍTICAS

# BOT_TOKEN es esencial
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ NO BOT_TOKEN PROVIDED")
    raise ValueError("BOT_TOKEN environment variable is required")

# 👑 ID del Administrador Supremo: Debe ser un número entero.
# Lo cargamos del entorno. Si no está, usamos un valor por defecto (ej. 6288842089).
ADMIN_SUPREMO_ID_STR = os.getenv('ADMIN_SUPREMO_ID', '6288842089')
try:
    ADMIN_SUPREMO_ID = int(ADMIN_SUPREMO_ID_STR)
except ValueError:
    logger.error("❌ ADMIN_SUPREMO_ID debe ser un número entero.")
    raise ValueError("ADMIN_SUPREMO_ID must be an integer.")

# 👑 Nombre del Administrador Supremo: Cargado del entorno.
ADMIN_SUPREMO = os.getenv('ADMIN_SUPREMO', 'Admin Supremo')


# --- CONSTANTES DE ESTADO Y ROL (FSM) ---
# Estas constantes son necesarias para las importaciones en registro.py

# Estados del Proceso de Registro
STATE_WAITING_LANGUAGE = 'waiting_language'
STATE_WAITING_NAME = 'waiting_name'
STATE_WAITING_PHONE = 'waiting_phone' 
STATE_WAITING_ROLE = 'waiting_role'
STATE_WAITING_PROVINCIA = 'waiting_provincia'
STATE_WAITING_ZONAS = 'waiting_zonas'
STATE_ACTIVE = 'active'
STATE_BANNED = 'banned'

# Roles de Usuario
ROLE_PENDIENTE = 'pendiente'
ROLE_SOLICITANTE = 'solicitante'
ROLE_TRANSPORTISTA = 'transportista'
ROLE_AMBOS = 'ambos'

# --- 🚨 CONSTANTES DE CATEGORÍAS (Solución al error 'CATEGORIES') 🚨 ---
CATEGORIES = {
    'CARGO_TIPO': [
        'Paquete pequeño', 
        'Caja mediana', 
        'Mueble grande', 
        'Material de construcción', 
        'Especial/Otro'
    ],
    'VEHICULO_TIPO': [
        'Moto/Bicicleta', 
        'Auto/Camioneta', 
        'Camión pequeño (hasta 2T)', 
        'Camión grande (más de 2T)'
    ]
}
# --- FIN DE CONSTANTES DE CATEGORÍAS ---


# Diccionarios multiidioma
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
        
        # Nuevos mensajes de error
        'error_no_permission': "❌ *Acceso denegado*. No tienes permisos para esta acción.",
        'error_not_registered': "❌ No estás registrado. Usa /start o /registro para empezar.",
        
        # Botones (Se manejan en keyboards.py, pero los textos de respuesta aquí)
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
        # ... (Mantener o adaptar si es necesario)
    }
}
