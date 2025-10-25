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
        # Permite acceder a los resultados por nombre de columna
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error conectando a la base de datos {DATABASE_FILE}: {e}")
        # Lanza una excepción para detener la operación si la conexión falla
        raise ConnectionError(f"No se pudo conectar a la DB: {e}")
# -------------------------------------------------------------

def init_db():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # --- 1. CREACIÓN DE TABLAS (Se mantiene igual) ---

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

            # TABLAS GEOGRÁFICAS, SOLICITUDES, VEHÍCULOS, AUDITORÍA (Aquí van las demás tablas...)
            # ... (asumiendo que las tablas restantes están definidas) ...
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

            # --- 2. INSERCIÓN DEL ADMINISTRADOR SUPREMO (Lógica simplificada y robusta) ---

            # Insertar/Actualizar al Admin Supremo en la tabla de usuarios
            # 🚨 CORRECCIÓN: Usamos None para 'username' y ADMIN_SUPREMO para 'nombre_completo'
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, estado)
                VALUES (?, ?, ?, ?, ?, 'activo')
            ''', (ADMIN_SUPREMO_ID, None, ADMIN_SUPREMO, "N/A", "ambos"))

            # Obtener el ID interno del usuario supremo
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (ADMIN_SUPREMO_ID,))
            admin_user_id_row = cursor.fetchone()
            
            if admin_user_id_row:
                admin_user_id = admin_user_id_row[0]
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

# 🚨 FUNCIÓN FALTANTE (Soluciona el ImportError en solicitudes.py) 🚨
def get_user_by_telegram_id(telegram_id):
    """
    Obtiene todos los datos del usuario de la tabla 'usuarios' por su telegram_id.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (telegram_id,))
            # Como row_factory está configurado, retorna un objeto Row (diccionario)
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error obteniendo usuario por telegram_id {telegram_id}: {e}")
        return None

def get_user_internal_id(telegram_id):
    """
    Obtiene el ID interno (PRIMARY KEY) de la tabla 'usuarios'.
    """
    user_data = get_user_by_telegram_id(telegram_id)
    return user_data['id'] if user_data else None

# Nota: Otras funciones como get_user_language, set_user_state, etc., deben estar aquí.
# Si usas set_user_state y get_user_state en registro.py, deben definirse aquí
# para evitar dependencias circulares con registro.py.
# Ya definimos get_user_by_telegram_id para el error actual.
