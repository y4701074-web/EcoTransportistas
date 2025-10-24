# main.py
import os
import time
from flask import Flask, request, abort 
import telebot 
from telebot.types import Update 

from config import logger
from db import init_db
from scheduler import init_scheduler
from bot_instance import bot

# --- Importar Handlers (Esto registra las funciones con el bot) ---
import handlers.registro
import handlers.general
import handlers.solicitudes
import handlers.transportista
import handlers.solicitante
import handlers.admin

# === CONFIGURACIÓN DE WEBHOOKS Y FLASK ===

KOYEB_URL = os.getenv("KOYEB_URL") 
BOT_TOKEN = os.getenv("BOT_TOKEN") 

if not BOT_TOKEN:
    logger.error("❌ Error: Variable de entorno BOT_TOKEN no encontrada.")
    exit(1)

WEBHOOK_PATH = f"/{BOT_TOKEN}"
PORT = int(os.getenv("PORT", 8080))

app = Flask(__name__)

# === ENDPOINT PARA TELEGRAM WEBHOOKS (CRÍTICO PARA KOYEB) ===
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        try:
            update = Update.de_json(json_string) 
            bot.process_new_updates([update])
            return 'OK', 200
        except Exception as e:
            logger.error(f"❌ Error al procesar update de Telegram: {e}")
            return 'Error', 500
    else:
        abort(403)

# === ENDPOINT PARA HEALTH CHECK ===
@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

# === FUNCIÓN PRINCIPAL (Modo Webhook) ===
def main_webhook():
    logger.info("🚀 Iniciando EcoTransportistas Bot (Modo Webhook)...")

    if init_db():
        logger.info("✅ Base de datos lista")
    else:
        logger.error("❌ Error crítico con base de datos. Saliendo.")
        return

    init_scheduler()

    if KOYEB_URL:
        bot.remove_webhook()
        time.sleep(1) 
        webhook_url = f"{KOYEB_URL}{WEBHOOK_PATH}"
        if bot.set_webhook(url=webhook_url):
             logger.info(f"✅ Webhook configurado en Telegram: {webhook_url}")
        else:
            logger.error(f"❌ Fallo al configurar Webhook en Telegram.")
            return

    logger.info(f"🤖 Bot iniciado - Escuchando en 0.0.0.0:{PORT}...")
    try:
        app.run(host="0.0.0.0", port=PORT, debug=False) 
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar servidor Flask: {e}")

if __name__ == '__main__':
    main_webhook()
