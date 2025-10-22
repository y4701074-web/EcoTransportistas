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

import http.server
import socketserver
import threading
import os

# === SERVICIO WEB MUY SIMPLE ===
class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    port = 8000
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        print(f"✅ Health server running on port {port}")
        httpd.serve_forever()

# === INICIAR TODO ===
if __name__ == '__main__':
    # Iniciar health server en hilo separado
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Tu código existente del bot
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