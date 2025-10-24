# bot_instance.py
import os
import telebot
from config import logger

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN no encontrado. No se puede inicializar el bot.")
    bot = None
else:
    try:
        # Se usa 'HTML' como parse_mode por defecto
        bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
        logger.info("✅ Instancia del bot creada.")
    except Exception as e:
        logger.error(f"❌ Error al inicializar TeleBot: {e}")
        bot = None
