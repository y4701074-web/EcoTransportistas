# config.py
import logging
import os
from dotenv import load_dotenv

# Nota: load_dotenv() se mantiene para pruebas locales, pero Koyeb usará sus propias variables.
load_dotenv()

# --- Configuración de Logging ---
def setup_logging():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.getLogger('telebot').setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("EcoTransportistasBot")

# --- Constantes del Sistema ---

# ID del Administrador Supremo (@Y_0304)
# **CRÍTICO:** Debes establecer ADMIN_SUPREMO_ID en Koyeb con el ID numérico de tu cuenta.
ADMIN_SUPREMO_ID = int(os.getenv("ADMIN_SUPREMO_ID", "0")) # Usar 0 como default seguro
ADMIN_SUPREMO_USERNAME = "@Y_0304"

# Roles de Usuario
ROLE_SOLICITANTE = 'SOLICITANTE'
ROLE_TRANSPORTISTA = 'TRANSPORTISTA'
ROLE_AMBOS = 'AMBOS' # Solicitante + Transportista

# Estados de Registro (Para el Flujo Corregido)
STATE_WAITING_LANGUAGE = 'WAIT_LANG'
STATE_WAITING_NAME = 'WAIT_NAME'
STATE_WAITING_PHONE = 'WAIT_PHONE'
STATE_WAITING_ROLE = 'WAIT_ROLE'
STATE_WAITING_PROVINCIA = 'WAIT_PROVINCIA' # Opcional
STATE_WAITING_ZONAS = 'WAIT_ZONAS' # Opcional
STATE_ACTIVE = 'ACTIVE'

# Nuevas Categorías de Carga
CATEGORIES = {
    1: "Transporte de personas", 
    2: "Carga ligera (Hasta 20kg)",          
    3: "Carga pesada (20kg - 500kg)",          
    4: "Mega carga (500kg+)"            
}
