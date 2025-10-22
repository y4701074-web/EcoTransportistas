from config import logger
from db import init_db
from scheduler import init_scheduler
from bot_instance import bot

# --- Importar Handlers ---
import handlers.registro
import handlers.general
import handlers.solicitudes
import handlers.transportista
import handlers.solicitante
import handlers.admin

# === AGREGAR ESTAS IMPORTACIONES ===
import multiprocessing
import time
import http.server
import socketserver

# === SERVICIO WEB EN PROCESO SEPARADO ===
def health_server_process():
    """Servidor web que corre en proceso separado para health checks"""
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
        
        def log_message(self, format, *args):
            # Silenciar logs del servidor HTTP
            pass
    
    port = 8000
    try:
        with socketserver.TCPServer(("", port), HealthHandler) as httpd:
            logger.info(f"✅ Health server running on port {port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"❌ Error en health server: {e}")

# === FUNCIÓN PRINCIPAL MODIFICADA ===
def main():
    logger.info("🚀 Iniciando EcoTransportistas Bot...")
    
    # === INICIAR SERVIDOR HEALTH CHECKS PRIMERO ===
    logger.info("🔄 Iniciando servidor health checks...")
    health_process = multiprocessing.Process(target=health_server_process)
    health_process.daemon = True
    health_process.start()
    
    # Esperar a que el servidor web esté listo
    time.sleep(3)
    logger.info("✅ Servidor health checks iniciado")
    
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
        main()  # Reiniciar en caso de error

if __name__ == '__main__':
    main()