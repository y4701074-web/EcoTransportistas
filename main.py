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

import multiprocessing
import os
import time
import http.server
import socketserver

# === SERVICIO WEB EN PROCESO SEPARADO ===
def health_server_process():
    """Servidor web que corre en proceso separado"""
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path in ['/health', '/']:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'OK')
            else:
                self.send_response(404)
                self.end_headers()
    
    port = 8000
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        print(f"✅ Health server running on port {port}")
        httpd.serve_forever()

# === INICIAR TODO ===
if __name__ == '__main__':
    # INICIAR SERVIDOR WEB PRIMERO (en proceso separado)
    health_process = multiprocessing.Process(target=health_server_process)
    health_process.daemon = True
    health_process.start()
    
    print("🔄 Servidor health check iniciado...")
    time.sleep(2)  # Dar tiempo a que el servidor arranque
    
    # LUEGO INICIAR EL BOT
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