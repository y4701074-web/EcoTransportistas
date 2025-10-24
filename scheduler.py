# scheduler.py
import threading
import time
from config import logger 

def tarea_limpieza_solicitudes():
    logger.info("🧹 Ejecutando tarea de limpieza de solicitudes programada.")
    # Aquí iría la lógica para eliminar solicitudes antiguas o procesar pagos.
    pass

def init_scheduler():
    def run_scheduled_jobs():
        logger.info("⚙️ Hilo del Scheduler iniciado y corriendo.")
        while True:
            # Ejemplo de ejecución periódica
            tarea_limpieza_solicitudes()
            time.sleep(3600) # Ejecutar cada hora

    scheduler_thread = threading.Thread(target=run_scheduled_jobs, daemon=True)
    scheduler_thread.start()
    logger.info("✅ Scheduler inicializado en un hilo 'daemon'.")
