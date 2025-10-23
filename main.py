import os
import time
from flask import Flask, request, abort # Necesitas Flask
import telebot # Si tu bot es pyTelegramBotAPI, necesitas acceder a telebot.types.Update

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

# === CONFIGURACIÓN DE WEBHOOKS Y FLASK ===
# Koyeb expone la URL principal a través de variables de entorno o el nombre de tu servicio.
# Usamos una variable de entorno KOYEB_URL para simplificar, si no existe, toma la de ejemplo.
# En el ambiente de Koyeb, esta variable debe apuntar a la URL de tu servicio.
KOYEB_URL = os.getenv("KOYEB_URL") # Ejemplo: https://mi-bot-telegram-xxxx.koyeb.app
BOT_TOKEN = os.getenv("BOT_TOKEN") # Asegúrate de tener esta variable en Koyeb

if not BOT_TOKEN:
    logger.error("❌ Error: Variable de entorno BOT_TOKEN no encontrada.")
    exit(1)

# Usamos el token como parte de la ruta secreta para mayor seguridad
WEBHOOK_PATH = f"/{BOT_TOKEN}"
# El puerto es dinámico en Koyeb, típicamente 8080 si no se especifica.
PORT = int(os.getenv("PORT", 8080))

# Crear la aplicación Flask
app = Flask(__name__)

# === ENDPOINT PARA TELEGRAM WEBHOOKS ===
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    # Solo procesar peticiones POST con el tipo de contenido correcto
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        try:
            # Procesar la actualización con la librería de tu bot
            update = telebot.types.Update.de_json(json_string) 
            bot.process_new_updates([update])
            return 'OK', 200
        except Exception as e:
            logger.error(f"❌ Error al procesar update de Telegram: {e}")
            return 'Error', 500
    else:
        # Petición no autorizada
        abort(403)

# === ENDPOINT PARA HEALTH CHECK (Ruta simple) ===
@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

# === FUNCIÓN PRINCIPAL (Modo Webhook) ===
def main_webhook():
    logger.info("🚀 Iniciando EcoTransportistas Bot (Modo Webhook)...")

    # 1. Inicializar base de datos
    if init_db():
        logger.info("✅ Base de datos lista")
    else:
        logger.error("❌ Error crítico con base de datos. Saliendo.")
        return

    # 2. Inicializar scheduler
    init_scheduler()

    # 3. Configurar el Webhook en la API de Telegram
    if KOYEB_URL:
        # Eliminar cualquier Webhook anterior
        bot.remove_webhook()
        time.sleep(1) # Pequeña espera
        
        # Configurar el nuevo Webhook
        webhook_url = f"{KOYEB_URL}{WEBHOOK_PATH}"
        if bot.set_webhook(url=webhook_url):
             logger.info(f"✅ Webhook configurado en Telegram: {webhook_url}")
        else:
            logger.error(f"❌ Fallo al configurar Webhook en Telegram.")
            return

    # 4. Iniciar el servidor web de Flask para escuchar peticiones
    logger.info(f"🤖 Bot iniciado - Escuchando en 0.0.0.0:{PORT}...")
    try:
        # host="0.0.0.0" es crucial para Koyeb/Docker
        app.run(host="0.0.0.0", port=PORT) 
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar servidor Flask: {e}")

if __name__ == '__main__':
    main_webhook()
