# main.py
import os
import time
from flask import Flask, request, abort # Necesitas Flask
import telebot 
from telebot.types import Update # Para acceder a telebot.types.Update

from config import logger # Incluye logging y constantes
from db import init_db
from scheduler import init_scheduler
from bot_instance import bot

# --- Importar Handlers --- (Esto registra los comandos y flujos)
import handlers.registro
import handlers.general
import handlers.solicitudes
import handlers.transportista
import handlers.solicitante
import handlers.admin

# === CONFIGURACIÓN DE WEBHOOKS Y FLASK ===

# Las variables de entorno serán inyectadas por Koyeb.com
KOYEB_URL = os.getenv("KOYEB_URL") 
BOT_TOKEN = os.getenv("BOT_TOKEN") 

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
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        try:
            update = Update.de_json(json_string) 
            # Procesar la actualización con la librería del bot
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

    # 1. Inicializar base de datos (con esquema corregido)
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
        time.sleep(1) 
        
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
        # host="0.0.0.0" es CRUCIAL para Koyeb/Docker
        app.run(host="0.0.0.0", port=PORT, debug=False) 
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar servidor Flask: {e}")

if __name__ == '__main__':
    main_webhook()
