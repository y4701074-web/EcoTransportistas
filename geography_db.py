import sqlite3
import json
from config import logger
from db import DATABASE_FILE, get_user_internal_id

def get_geographic_level_name(level, id_):
    """Obtiene el nombre de un país, provincia o zona dado su ID y nivel."""
    if not id_:
        return "N/A"
        
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            table = f"{level}s" # paises, provincias, zonas
            
            cursor.execute(f"SELECT nombre FROM {table} WHERE id = ?", (id_,))
            result = cursor.fetchone()
            return result[0] if result else "Desconocido"
            
    except Exception as e:
        logger.error(f"Error obteniendo nombre geográfico para {level} ID {id_}: {e}")
        return "ERROR_DB"

def get_available_countries_for_registration():
    """Obtiene todos los países activos para que los nuevos usuarios se registren."""
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Orden alfabético
            cursor.execute("SELECT id, nombre FROM paises WHERE estado = 'activo' ORDER BY nombre ASC")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo países disponibles: {e}")
        return []

def get_admin_creatable_countries(telegram_id):
    """Obtiene los países que un administrador tiene permiso para crear/gestionar."""
    user_internal_id = get_user_internal_id(telegram_id)
    if not user_internal_id:
        return []

    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Solo el Admin Supremo o Supremo 2 puede crear nuevos países
            cursor.execute('''
                SELECT a.nivel FROM administradores a 
                WHERE a.usuario_id = ? AND a.estado = 'activo'
            ''', (user_internal_id,))
            
            admin_data = cursor.fetchone()
            
            if admin_data and admin_data['nivel'] in ('supremo', 'supremo_2'):
                # Si es Supremo, puede ver todos los países creados para gestionarlos
                cursor.execute("SELECT id, nombre FROM paises ORDER BY nombre ASC")
                return cursor.fetchall()
            
            return []
    except Exception as e:
        logger.error(f"Error obteniendo países gestionables por admin {telegram_id}: {e}")
        return []
