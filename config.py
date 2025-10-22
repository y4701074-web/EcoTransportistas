import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración - SEGURO
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ NO BOT_TOKEN PROVIDED")
    raise ValueError("BOT_TOKEN environment variable is required")

ADMIN_SUPREMO = os.environ.get('ADMIN_SUPREMO', 'Y_0304').lstrip('@')

# Diccionarios multiidioma
MESSAGES = {
    'es': {
        'welcome': "🚀 *¡Bienvenido a EcoTransportistas!* 🌟\n\n👋 Hola {name}!\n\n🌍 *¿Qué es EcoTransportistas?*\nEs tu plataforma para conectar *transportistas* con *personas que necesitan enviar cosas* en toda Cuba.\n\n📦 *¿Eres Solicitante?* → Encuentra transporte rápido y confiable\n🚚 *¿Eres Transportista?* → Consigue más clientes en tu zona\n\n🛠️ *¿Cómo empezar?*\n1️⃣ Usa /registro para crear tu perfil\n2️⃣ Elige tu tipo de usuario\n3️⃣ ¡Comienza a conectar!",
        'choose_language': "🌍 *Selecciona tu idioma / Choose your language:*",
        'registration_start': "📝 *Iniciando registro...*\n\nPor favor comparte tu número de teléfono para verificar tu identidad:",
        'phone_received': "✅ *Teléfono verificado: {phone}*\n\n📛 Ahora ingresa tu *nombre completo* (como aparece en tu documento):",
        'name_received': "✅ *Nombre registrado: {name}*\n\n🚀 *Selecciona tu tipo de usuario:*",
        'choose_user_type': "¿Qué rol deseas tener en el sistema?",
        'transportista_selected': "🚚 *¡Excelente! Eres ahora Transportista*\n\n📍 Ahora selecciona tu *provincia base* de operación:",
        'solicitante_selected': "📦 *¡Perfecto! Eres ahora Solicitante*\n\n📍 Ahora selecciona tu *provincia base*:",
        'both_selected': "🎯 *¡Fantástico! Tienes ambos roles*\n\n📍 Ahora selecciona tu *provincia base*:",
        'provincia_selected': "✅ *Provincia seleccionada: {provincia}*\n\n🗺️ Ahora selecciona tu *zona específica*:",
        'zona_selected': "🎉 *¡Registro Completado!*\n\n✅ Tu perfil ha sido creado exitosamente.\n\n📊 *Tu información:*\n👤 Nombre: {name}\n📞 Teléfono: {phone}\n🎯 Tipo: {tipo}\n📍 Provincia: {provincia}\n🗺️ Zona: {zona}\n\n¡Ya puedes usar todas las funciones del sistema!",
        'new_request': "📦 *Nueva Solicitud de Transporte*\n\nPor favor completa la información paso a paso:",
        'request_vehicle_type': "🚚 *Selecciona el tipo de vehículo requerido:*",
        'request_cargo_type': "📦 *Tipo de carga:*",
        'request_description': "✏️ *Describe detalladamente lo que necesitas transportar:*",
        'request_weight': "⚖️ *Peso y dimensiones aproximadas:*",
        'request_pickup': "📍 *Dirección exacta de *RECOGIDA*:*\n(Escribe la dirección completa)",
        'request_delivery': "🎯 *Dirección exacta de *ENTREGA*:*\n(Escribe la dirección completa)",
        'request_budget': "💰 *Presupuesto que ofreces (en CUP):*",
        'request_summary': "📋 *Resumen de tu solicitud:*\n\n{summary}\n\n¿Confirmas la publicación?",
        'request_published': "✅ *¡Solicitud publicada exitosamente!*\n\nLos transportistas de tu zona han sido notificados.",
        'request_received': "🚚 *Nueva solicitud en tu zona!*\n\n{details}\n\n¿Aceptas este trabajo?",
        'request_accepted': "✅ *Has aceptado la solicitud*\n\nEspera confirmación del solicitante...",
        'request_confirmed': "🎉 *¡Solicitud confirmada!*\n\n📞 Contacta al solicitante: {phone}",
        'request_rejected': "❌ Solicitud rechazada o expirada",
        'admin_panel': "👑 *Panel de Administración*",
        'error_generic': "❌ Error en el sistema. Intenta nuevamente.",
        'main_menu': "🎯 *Menú Principal* - Elige una opción:",
        'error_no_permission': "❌ No tienes permisos para esta acción",
        'error_not_solicitante': "❌ Solo los solicitantes pueden crear solicitudes",
        'error_not_transportista': "❌ Solo los transportistas pueden ver solicitudes",
        'no_requests_found': "📭 No hay solicitudes activas en tu zona actualmente.",
        'request_cancelled': "❌ Solicitud cancelada",
        'request_not_available': "❌ Esta solicitud ya no está disponible",
        'request_expired': "⏰ *Solicitud #{id} expirada*\n\nEl tiempo de confirmación ha expirado. La solicitud está disponible nuevamente.",
        'confirmation_sent': "✅ Solicitud aceptada. Espera confirmación...",
        'request_processed': "❌ Esta solicitud ya fue procesada",
        'request_confirmed_solicitante': "✅ *Solicitud confirmada exitosamente!*\n\nEl transportista ha sido notificado y pronto te contactará.",
    },
    'en': {
        # ... (puedes copiar toda la sección 'en' de tu archivo original aquí) ...
        'main_menu': "🎯 *Main Menu* - Choose an option:",
        'error_no_permission': "❌ You do not have permission for this action",
        'error_not_solicitante': "❌ Only requesters can create requests",
        'error_not_transportista': "❌ Only transporters can view requests",
        'no_requests_found': "📭 There are no active requests in your area currently.",
        'request_cancelled': "❌ Request cancelled",
        'request_not_available': "❌ This request is no longer available",
        'request_expired': "⏰ *Request #{id} expired*\n\nThe confirmation time has expired. The request is available again.",
        'confirmation_sent': "✅ Request accepted. Waiting for confirmation...",
        'request_processed': "❌ This request has already been processed",
        'request_confirmed_solicitante': "✅ *Request confirmed successfully!*\n\nThe transporter has been notified and will contact you shortly.",
    }
}

# Datos de prueba para provincias y zonas
PROVINCIAS_CUBA = {
    'PRI': 'Pinar del Río',
    'ART': 'Artemisa', 
    'HAB': 'La Habana',
    'MAY': 'Mayabeque',
    'MAT': 'Matanzas',
    'CFG': 'Cienfuegos',
    'VCL': 'Villa Clara',
    'SSP': 'Sancti Spíritus',
    'CAV': 'Ciego de Ávila',
    'CMG': 'Camagüey',
    'LTU': 'Las Tunas',
    'HOL': 'Holguín',
    'GRA': 'Granma',
    'SCU': 'Santiago de Cuba',
    'GTM': 'Guantánamo',
    'IJV': 'Isla de la Juventud'
}

ZONAS_POR_PROVINCIA = {
    'HAB': ['Habana Vieja', 'Centro Habana', 'Vedado', 'Miramar', 'Playa', 'Cerro'],
    'MAT': ['Matanzas Ciudad', 'Varadero', 'Cárdenas', 'Colón'],
    'VCL': ['Santa Clara', 'Placetas', 'Sagua la Grande', 'Remedios'],
    'HOL': ['Holguín Ciudad', 'Banes', 'Gibara', 'Moa'],
    'SCU': ['Santiago Centro', 'El Cobre', 'Palma Soriano', 'Contramaestre']
    # ... (agregar más zonas si es necesario) ...
}
