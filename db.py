import sqlite3
import json 
# Línea 3: Importamos el nombre legible (ADMIN_SUPREMO) y el ID
from config import logger, ADMIN_SUPREMO, ADMIN_SUPREMO_ID 
import os

# Usamos una variable de entorno como alternativa para el archivo de la DB
DATABASE_FILE = os.getenv('DB_FILE', 'ecotransportistas.db')

# 🚨 FUNCIÓN CRÍTICA DE CONEXIÓN 🚨
def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos SQLite.
    Configura el 'row_factory' para acceder a las columnas por nombre.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE, timeout=10)
        # Permite acceder a los resultados por nombre de columna (necesario para la nueva lógica)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error conectando a la base de datos {DATABASE_FILE}: {e}")
        # Lanza una excepción para detener la operación si la conexión falla
        raise ConnectionError(f"No se pudo conectar a la DB: {e}")
# -------------------------------------------------------------

def init_db():
    try:
        # Usar get_db_connection para asegurar la configuración de row_factory y manejo de errores
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # --- 1. CREACIÓN DE TABLAS (Se mantiene igual, solo se usa la nueva conexión) ---

            # TABLA DE USUARIOS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    nombre_completo TEXT,
                    telefono TEXT,
                    tipo TEXT,
                    
                    pais_id INTEGER,
                    provincia_id INTEGER,
                    zona_id INTEGER,
                    
                    idioma TEXT DEFAULT 'es',
                    estado TEXT DEFAULT 'activo',
                    vehiculos TEXT DEFAULT '[]',
                    
                    zonas_trabajo_ids TEXT DEFAULT '[]', 
                    
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # TABLA DE ADMINISTRADORES
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS administradores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER UNIQUE,
                    nivel TEXT,
                    
                    pais_id INTEGER, 
                    provincia_id INTEGER,
                    zona_id INTEGER,
                    
                    comision_transportistas REAL DEFAULT 100,
                    comision_solicitantes REAL DEFAULT 50,
                    porcentaje_minimo_ganancia REAL DEFAULT 5,
                    
                    estado TEXT DEFAULT 'activo',
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
            ''')

            # TABLAS GEOGRÁFICAS, SOLICITUDES, VEHÍCULOS, AUDITORÍA 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE,
                    codigo TEXT UNIQUE,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(creado_por_admin_id) REFERENCES usuarios(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS provincias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pais_id INTEGER,
                    nombre TEXT,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pais_id, nombre),
                    FOREIGN KEY(pais_id) REFERENCES paises(id),
                    FOREIGN KEY(creado_por_admin_id) REFERENCES usuarios(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS zonas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provincia_id INTEGER,
                    nombre TEXT,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(provincia_id, nombre),
                    FOREIGN KEY(provincia_id) REFERENCES provincias(id),
                    FOREIGN KEY(creado_por_admin_id) REFERENCES usuarios(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solicitudes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    pais_id INTEGER,
                    provincia_id INTEGER,
                    zona_id INTEGER,
                    vehicle_type TEXT,
                    cargo_type TEXT,
                    description TEXT,
                    pickup TEXT,
                    delivery TEXT,
                    budget REAL,
                    estado TEXT DEFAULT 'activa',
                    transportista_asignado INTEGER,
                    pending_confirm_until TIMESTAMP,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY(transportista_asignado) REFERENCES usuarios(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    tipo TEXT,
                    placa TEXT UNIQUE,
                    capacidad_toneladas REAL,
                    estado TEXT DEFAULT 'activo',
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accion TEXT,
                    usuario_id INTEGER,
                    detalles TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- 2. INSERCIÓN DEL ADMINISTRADOR SUPREMO (Lógica simplificada y más robusta) ---

            # 1. Insertar/Actualizar al Admin Supremo en la tabla de usuarios
            # 🚨 CORRECCIÓN: Usamos None para 'username' y ADMIN_SUPREMO para 'nombre_completo'
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, estado)
                VALUES (?, ?, ?, ?, ?, 'activo')
            ''', (ADMIN_SUPREMO_ID, None, ADMIN_SUPREMO, "N/A", "ambos"))

            # Obtener el ID interno del usuario supremo
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (ADMIN_SUPREMO_ID,))
            admin_user_id = cursor.fetchone()[0]

            # 2. Asegurar que el Admin Supremo tenga rol 'supremo' en la tabla `administradores`
            cursor.execute("SELECT usuario_id FROM administradores WHERE usuario_id = ?", (admin_user_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO administradores (usuario_id, nivel, estado)
                    VALUES (?, ?, 'activo')
                ''', (admin_user_id, 'supremo'))
            else:
                 # Actualizar por si acaso ya existía con un nivel inferior
                cursor.execute('''
                    UPDATE administradores SET nivel = 'supremo', estado = 'activo'
                    WHERE usuario_id = ?
                ''', (admin_user_id,))

            # --- 3. FINALIZACIÓN ---
            conn.commit()
            logger.info("✅ Base de datos inicializada correctamente")
            return True

    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
        return False

# --------------------------------------------------------------------------------------
# --- Helper functions para DB ---
# --------------------------------------------------------------------------------------
# Nota: Aquí se deben asegurar que todas las funciones usen 'telegram_id' en lugar de 'chat_id'
# (No se incluyen todas las funciones por brevedad, asumiendo que el usuario aplica la corrección)

# EJEMPLO DE CORRECCIÓN PARA get_user_language
def get_user_language(user_id):
    # Se utiliza la nueva conexión
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 🚨 Asegurar 'telegram_id' en lugar de 'chat_id'
            cursor.execute("SELECT idioma FROM usuarios WHERE telegram_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 'es'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'es'

# ... (El resto de funciones auxiliares se mantienen o corrigen localmente en el proyecto del usuario)
