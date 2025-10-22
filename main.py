from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    
    def log_message(self, format, *args):
        pass  # Silenciar logs

def start_health_server():
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

# Iniciar servidor de health check
if __name__ == '__main__':
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Tu código actual del bot...


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
