# db.py
import sqlite3
from config import logger
import os

DB_NAME = "ecotransportistas.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)

# Esquema de la Base de Datos basado en el informe
SCHEMA = """
-- 👑 config_global: Configuración del sistema
CREATE TABLE IF NOT EXISTS config_global (
    clave TEXT PRIMARY KEY,
    valor TEXT
);

-- 🌍 paises, 🏙️ provincias, 🗺️ zonas: Jerarquía territorial
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
    FOREIGN KEY(admin_id) REFERENCES usuarios(id),
    UNIQUE(nombre, pais_id)
);

CREATE TABLE IF NOT EXISTS zonas (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    provincia_id INTEGER,
    admin_id INTEGER,
    FOREIGN KEY(provincia_id) REFERENCES provincias(id),
    FOREIGN KEY(admin_id) REFERENCES usuarios(id),
    UNIQUE(nombre, provincia_id)
);

-- 👤 usuarios: Todos los usuarios registrados
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY, 
    chat_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    nombre TEXT,
    telefono TEXT,
    idioma TEXT DEFAULT 'ES',
    rol TEXT NOT NULL,          -- SOLICITANTE, TRANSPORTISTA, AMBOS
    estado TEXT,                -- WAIT_LANG, WAIT_ROLE, ACTIVE, etc.
    es_admin INTEGER DEFAULT 0, -- 0: No, 1: País, 2: Provincia, 3: Zona, 9: Supremo
    provincia_base_id INTEGER,  -- Opcional
    zonas_base TEXT,            -- Zonas base (IDs separadas por coma, opcional)
    FOREIGN KEY(provincia_base_id) REFERENCES provincias(id)
);

-- 🚚 Configuracion de Transportistas
CREATE TABLE IF NOT EXISTS transportista_config (
    user_id INTEGER PRIMARY KEY,
    categorias TEXT NOT NULL,  -- IDs de CATEGORIES separadas por coma (1,2,3,4)
    zonas_servicio TEXT,       -- IDs de ZONAS separadas por coma (opcional)
    vehiculos TEXT,            -- Nombres/IDs de vehículos específicos
    FOREIGN KEY(user_id) REFERENCES usuarios(id)
);


-- 📦 solicitudes: Solicitudes activas
CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER PRIMARY KEY,
    solicitante_id INTEGER,
    categoria INTEGER NOT NULL,
    datos_especificos TEXT,
    direccion_origen TEXT NOT NULL,
    direccion_destino TEXT NOT NULL,
    provincia_id INTEGER,
    zona_id INTEGER,
    estado TEXT, -- ACTIVA, CERRADA, EN_PROCESO
    FOREIGN KEY(solicitante_id) REFERENCES usuarios(id),
    FOREIGN KEY(provincia_id) REFERENCES provincias(id),
    FOREIGN KEY(zona_id) REFERENCES zonas(id)
);

-- 📂 solicitudes_cerradas: Historial
CREATE TABLE IF NOT EXISTS solicitudes_cerradas (
    id INTEGER PRIMARY KEY,
    solicitud_id INTEGER UNIQUE,
    transportista_id INTEGER,
    comision_aplicada REAL,
    fecha_cierre DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(solicitud_id) REFERENCES solicitudes(id),
    FOREIGN KEY(transportista_id) REFERENCES usuarios(id)
);

-- 💰 pagos (control de comisiones y rentas)
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    monto REAL,
    tipo TEXT, -- COMISION_RECIBIDA, RENTA_PAGADA
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES usuarios(id)
);

-- 📊 auditoria (registro de auditoría)
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    accion TEXT NOT NULL,
    detalles TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db_connection():
    """Retorna una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
    return conn

def init_db():
    """Inicializa la base de datos y crea el esquema si no existe."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ejecutar el esquema de creación de tablas
        cursor.executescript(SCHEMA)
        
        # Corrección: Asegurar que el ADMIN SUPREMO exista en la tabla usuarios si no está.
        # Esto es CRÍTICO para resolver el "Problema: @Y_0304 no es reconocido como admin supremo"
        # NOTA: Debes sustituir 'ADMIN_SUPREMO_ID' con el ID real de tu cuenta.
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios (id, chat_id, username, rol, estado, es_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ADMIN_SUPREMO_ID, ADMIN_SUPREMO_ID, ADMIN_SUPREMO_USERNAME, 'ADMIN', 'ACTIVE', 9))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Base de datos SQLite '{DB_NAME}' lista y esquema inicializado.")
        return True
    except Exception as e:
        logger.error(f"❌ Error crítico al inicializar la DB en {DB_PATH}: {e}")
        return False
