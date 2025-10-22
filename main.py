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

from flask import Flask
import threading
import os

# === SERVICIO WEB PARA HEALTH CHECKS ===
def create_health_server():
    """Servidor simple para que Koyeb verifique que la app está viva"""
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return '✅ EcoTransportistas Bot está funcionando!'
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'ecotransportistas-bot'}, 200
    
    # Usar el puerto que Koyeb espera (8000)
    port = int(os.environ.get('PORT', 8000))
    print(f"🔄 Iniciando servidor health check en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

# === INICIAR TODO ===
if __name__ == '__main__':
    # Iniciar servidor de health checks en segundo plano
    health_thread = threading.Thread(target=create_health_server, daemon=True)
    health_thread.start()
    
    # Tu código existente del bot (NO lo modifiques)
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
