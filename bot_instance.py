import telebot
from config import BOT_TOKEN

# Inicializar bot
bot = telebot.TeleBot(BOT_TOKEN)

# Estados para FSM (Finite State Machine)
user_states = {}
