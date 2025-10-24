# db.py
import sqlite3
from config import logger, ADMIN_SUPREMO_ID, ADMIN_SUPREMO_USERNAME
import os

DB_NAME = "ecotransportistas.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)

SCHEMA = """
-- 👑 config_global
CREATE TABLE IF NOT EXISTS config_global (clave TEXT PRIMARY KEY, valor TEXT);

-- 🌍 paises, 🏙️ provincias, 🗺️ zonas
CREATE TABLE IF NOT EXISTS paises (
    id INTEGER PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    admin_id INTEGER,
    FOREIGN KEY(admin_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS provincias (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    pais_id INTEGER,
    admin_id INTEGER,
    FOREIGN KEY(pais_id) REFERENCES paises(id),
    FOREIGN KEY(admin_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS zonas (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    provincia_id INTEGER,
    admin_id INTEGER,
    FOREIGN KEY(provincia_id) REFERENCES provincias(id),
    FOREIGN KEY(admin_id) REFERENCES usuarios(id)
);

-- 👤 usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY, 
    chat_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    nombre TEXT,
    telefono TEXT,
    idioma TEXT DEFAULT 'ES',
    rol TEXT NOT NULL DEFAULT 'SOLICITANTE',
    estado TEXT DEFAULT 'WAIT_LANG',
    es_admin INTEGER DEFAULT 0, -- 0: No, 9: Supremo
    provincia_base_id INTEGER,  -- Opcional
    zonas_base TEXT,            -- Opcional (IDs separadas por coma)
    FOREIGN KEY(provincia_base_id) REFERENCES provincias(id)
);

-- 🚚 Configuracion de Transportistas
CREATE TABLE IF NOT EXISTS transportista_config (
    user_id INTEGER PRIMARY KEY,
    categorias TEXT NOT NULL,  -- IDs de CATEGORIES separadas por coma
    zonas_servicio TEXT,       -- IDs de ZONAS de servicio
    vehiculos TEXT,            -- Vehículos específicos
    FOREIGN KEY(user_id) REFERENCES usuarios(id)
);

-- 📦 solicitudes
CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER PRIMARY KEY,
    solicitante_id INTEGER,
    categoria INTEGER NOT NULL,
    datos_especificos TEXT,
    direccion_origen TEXT NOT NULL,
    direccion_destino TEXT NOT NULL,
    provincia_id INTEGER,
    zona_id INTEGER,
    estado TEXT, -- ACTIVA, EN_PROCESO, CERRADA
    FOREIGN KEY(solicitante_id) REFERENCES usuarios(id)
);

-- 📂 solicitudes_cerradas, 💰 pagos, 📊 auditoria, etc. (Tablas adicionales)
CREATE TABLE IF NOT EXISTS solicitudes_cerradas (id INTEGER PRIMARY KEY, solicitud_id INTEGER UNIQUE, transportista_id INTEGER, comision_aplicada REAL);
CREATE TABLE IF NOT EXISTS pagos (id INTEGER PRIMARY KEY, user_id INTEGER, monto REAL, tipo TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY, user_id INTEGER, accion TEXT NOT NULL, detalles TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP);
"""

def get_db_connection():
    """Retorna una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Inicializa la base de datos y crea el esquema si no existe."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.executescript(SCHEMA)
        
        # Corrección Crítica: Asegurar que el ADMIN SUPREMO exista y tenga rol 9 (Supremo)
        if ADMIN_SUPREMO_ID != 0:
            cursor.execute("""
                INSERT OR REPLACE INTO usuarios (chat_id, username, rol, estado, es_admin)
                VALUES (?, ?, ?, ?, ?)
            """, (ADMIN_SUPREMO_ID, ADMIN_SUPREMO_USERNAME, 'ADMIN', 'ACTIVE', 9))
            
            # Nota: Usamos INSERT OR REPLACE para actualizar si ya existía el chat_id
            
            logger.info(f"✅ Admin Supremo ({ADMIN_SUPREMO_USERNAME}) asegurado en DB con ID: {ADMIN_SUPREMO_ID}.")

        conn.commit()
        conn.close()
        
        logger.info(f"✅ Base de datos SQLite '{DB_NAME}' lista y esquema inicializado.")
        return True
    except Exception as e:
        logger.error(f"❌ Error crítico al inicializar la DB en {DB_PATH}: {e}")
        return False
