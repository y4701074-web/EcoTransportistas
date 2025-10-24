# scheduler.py
import threading
import time
from config import logger 

def tarea_limpieza_solicitudes():
    logger.info("🧹 Ejecutando tarea de limpieza de solicitudes programada.")
    # Aquí iría la lógica para eliminar solicitudes antiguas de la DB.
    pass

def init_scheduler():
    def run_scheduled_jobs():
        logger.info("⚙️ Hilo del Scheduler iniciado y corriendo.")
        while True:
            # Aquí se ejecutarían las tareas programadas con un scheduler como APScheduler o schedule
            time.sleep(60) 

    scheduler_thread = threading.Thread(target=run_scheduled_jobs, daemon=True)
    scheduler_thread.start()
    logger.info("✅ Scheduler inicializado en un hilo 'daemon'.")
