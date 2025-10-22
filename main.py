from config import logger
from db import init_db
from scheduler import init_scheduler
from bot_instance import bot

# --- Importar Handlers ---
# ¡MUY IMPORTANTE! 
# Debes importar todos los módulos de handlers aquí
# para que los decoradores (@bot.message_handler) se registren.

import handlers.registro
import handlers.general
import handlers.solicitudes
import handlers.transportista
import handlers.solicitante
import handlers.admin

# -------------------------

# FUNCIÓN PRINCIPAL
def main():
    logger.info("🚀 Iniciando EcoTransportistas Bot...")
    
    # Inicializar base de datos
    if init_db():
        logger.info("✅ Base de datos lista")
    else:
        logger.error("❌ Error crítico con base de datos. Saliendo.")
        return
    
    # Inicializar scheduler
    init_scheduler()
    
    # Iniciar el bot
    try:
        logger.info("🤖 Bot iniciado - Escuchando mensajes...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"❌ Error crítico en el bot: {e}")
        logger.info("Reiniciando el bot...")
        main() # Reiniciar en caso de error

if __name__ == '__main__':
    main()

# TODO TU CÓDIGO ACTUAL DEL BOT (NO LO BORRES)
# ... [todo tu código existente] ...
# ... [tus handlers, funciones, etc.] ...
# ... [hasta el final del archivo] ...

# === AGREGAR ESTO AL FINAL DEL ARCHIVO ===
from flask import Flask
import threading
import os

def health_server():
    app = Flask(__name__)
    
    @app.route('/health')
    def health_check():
        return 'OK', 200
    
    @app.route('/')
    def home():
        return '✅ Bot funcionando'
    
    port = 8000
    app.run(host='0.0.0.0', port=port, debug=False)

# === ESTA PARTE FINAL REEMPLAZA LO QUE TENÍAS ===
if __name__ == '__main__':
    # Iniciar health server en hilo separado
    health_thread = threading.Thread(target=health_server, daemon=True)
    health_thread.start()
    
    # Tu código existente del bot (NO lo cambies)
    logger.info("🚀 Iniciando EcoTransportistas Bot en Koyeb...")
    
    if init_db():
        logger.info("✅ Base de datos lista")
    else:
        logger.error("❌ Error crítico con base de datos")
        exit(1)
    
    try:
        logger.info("🤖 Bot iniciado - Escuchando mensajes...")
        bot.infinity_polling(timeout=60)
    except Exception as e:
        logger.error(f"❌ Error en el bot: {e}")
