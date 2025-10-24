# main.py
import os
import time
from flask import Flask, request, abort
import telebot # Necesitas Flask
from telebot.types import Update 

# --- Módulos y configuración locales ---
# Importar config primero para asegurar que el logging y las variables esten listas
from config import logger 
from db import init_db
from scheduler import init_scheduler
from bot_instance import bot

# --- Importar Handlers (Esto registra las funciones con el bot) ---
# Al importar, se ejecutan las decoraciones @bot.message_handler
import handlers.registro
import handlers.general
import handlers.solicitudes
import handlers.transportista
import handlers.solicitante
import handlers.admin

# === CONFIGURACIÓN DE WEBHOOKS Y FLASK ===

KOYEB_URL = os.getenv("KOYEB_URL") 
BOT_TOKEN = os.getenv("BOT_TOKEN") 
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN:
    logger.error("❌ Error CRÍTICO: Variable de entorno BOT_TOKEN no encontrada.")
    exit(1)
if not KOYEB_URL:
    logger.warning("⚠️ Advertencia: KOYEB_URL no definida. El Webhook fallará en un entorno de producción.")

# Usamos el token como parte de la ruta secreta
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"{KOYEB_URL}{WEBHOOK_PATH}" if KOYEB_URL else None

# Crear la aplicación Flask
app = Flask(__name__)

# === ENDPOINT PARA TELEGRAM WEBHOOKS (CRÍTICO PARA KOYEB) ===
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        try:
            update = Update.de_json(json_string) 
            # Asegúrate de que la instancia del bot no sea None
            if bot:
                bot.process_new_updates([update])
                return 'OK', 200
            else:
                logger.error("❌ Bot no inicializado, no se puede procesar el update.")
                return 'Error', 500
        except Exception as e:
            logger.error(f"❌ Error al procesar update de Telegram: {e}")
            return 'Error', 500
    else:
        abort(403)

# === ENDPOINT PARA HEALTH CHECK (Ruta simple) ===
@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

# === FUNCIÓN PRINCIPAL (Modo Webhook) ===
def main_webhook():
    logger.info("🚀 Iniciando EcoTransportistas Bot (Modo Webhook)...")

    # 1. Inicializar base de datos
    if not init_db():
        logger.error("❌ Error crítico con base de datos. Saliendo.")
        return

    # 2. Inicializar scheduler
    init_scheduler()
    logger.info("✅ Base de datos y Scheduler listos.")

    # 3. Configurar el Webhook en la API de Telegram
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            time.sleep(0.5) 
            
            if bot.set_webhook(url=WEBHOOK_URL):
                 logger.info(f"✅ Webhook configurado en Telegram: {WEBHOOK_URL}")
            else:
                logger.error(f"❌ Fallo al configurar Webhook en Telegram.")
                return
        except Exception as e:
            logger.error(f"❌ Fallo al configurar Webhook: {e}")
            return
    else:
        logger.warning("⚠️ Saltando configuración de Webhook. No hay KOYEB_URL.")

    # 4. Iniciar el servidor web de Flask
    logger.info(f"🤖 Bot iniciado - Escuchando en 0.0.0.0:{PORT}...")
    try:
        app.run(host="0.0.0.0", port=PORT, debug=False) 
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar servidor Flask: {e}")

if __name__ == '__main__':
    main_webhook()
