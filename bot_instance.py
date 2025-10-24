# bot_instance.py
import telebot
from config import logger, BOT_TOKEN # Importamos el token de configu.py (config)

# -------------------------------------------------------------
# 🚨 SOLUCIÓN AL ImportError: user_states 🚨

# 1. Definición del Diccionario de Estados en Memoria
# Este diccionario almacena el estado temporal de los usuarios (ej. el FSM de administración)
user_states = {} 

# 2. Inicialización de la Instancia del Bot
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN no encontrado. No se puede inicializar el bot.")
    bot = None
else:
    try:
        # Usamos el BOT_TOKEN importado de config
        bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
        logger.info("✅ Instancia del bot creada.")
    except Exception as e:
        logger.error(f"❌ Error al inicializar TeleBot: {e}")
        bot = None

# NOTA: Aunque el código original usaba os.getenv() localmente, 
# se ha simplificado importando BOT_TOKEN desde configu.py para consistencia.
# Si el BOT_TOKEN no se pudo cargar en configu.py, el programa habría fallado antes.
# Usamos el bloque try/except por si falla la inicialización de telebot.
# -------------------------------------------------------------
