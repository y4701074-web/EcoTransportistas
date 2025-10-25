import sqlite3
import json 
import os
# Asegúrate de que config.py esté en el mismo directorio o en el PYTHONPATH
from config import logger, ADMIN_SUPREMO, ADMIN_SUPREMO_ID 

# --- CONFIGURACIÓN ---
# Usamos una variable de entorno como alternativa para el archivo de la DB
DATABASE_FILE = os.getenv('DB_FILE', 'ecotransportistas.db')

# --- CONEXIÓN Y UTILIDAD BÁSICA ---

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos SQLite.
    Configura el 'row_factory' para acceder a las columnas por nombre.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE, timeout=10)
        # Permite acceder a los resultados por nombre de columna (como un diccionario)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error conectando a la base de datos {DATABASE_FILE}: {e}")
        raise ConnectionError(f"No se pudo conectar a la DB: {e}")

# --- INICIALIZACIÓN DE LA BASE DE DATOS ---

def init_db():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # --- 1. CREACIÓN DE TABLAS ---

            # TABLA DE USUARIOS (telegram_id es la clave para la interacción con el bot)
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
                    estado TEXT DEFAULT 'pendiente', 
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
            
            # TABLAS GEOGRÁFICAS (Esqueletos básicos)
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE,
                    codigo TEXT UNIQUE,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    FOREIGN KEY(pais_id) REFERENCES paises(id)
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
                    FOREIGN KEY(provincia_id) REFERENCES provincias(id)
                )
            ''')


            # TABLA DE SOLICITUDES
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solicitudes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    solicitante_id INTEGER,
                    categoria TEXT,
                    tipo_carga TEXT,
                    descripcion TEXT,
                    
                    # IDs geográficos para Recogida y Entrega
                    pais_recogida_id INTEGER,
                    provincia_recogida_id INTEGER,
                    zona_recogida_id INTEGER,
                    
                    pais_entrega_id INTEGER,
                    provincia_entrega_id INTEGER,
                    zona_entrega_id INTEGER,
                    
                    presupuesto REAL,
                    estado TEXT DEFAULT 'pendiente', 
                    
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY(solicitante_id) REFERENCES usuarios(id)
                )
            ''')
            
            # TABLA DE VEHÍCULOS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    tipo TEXT,
                    placa TEXT UNIQUE,
                    capacidad_toneladas REAL,
                    estado TEXT DEFAULT 'activo', 
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
            ''')

            # --- 2. INSERCIÓN DEL ADMINISTRADOR SUPREMO ---

            # Insertar/Actualizar al Admin Supremo en la tabla de usuarios
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, estado)
                VALUES (?, ?, ?, ?, ?, 'activo')
            ''', (ADMIN_SUPREMO_ID, None, ADMIN_SUPREMO, "N/A", "ambos"))

            # Obtener el ID interno del usuario supremo
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (ADMIN_SUPREMO_ID,))
            admin_user_id_row = cursor.fetchone()
            
            if admin_user_id_row:
                admin_user_id = admin_user_id_row[0]
                # Asegurar que el Admin Supremo tenga rol 'supremo' en la tabla administradores
                cursor.execute("SELECT usuario_id FROM administradores WHERE usuario_id = ?", (admin_user_id,))
                
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO administradores (usuario_id, nivel, estado)
                        VALUES (?, ?, 'activo')
                    ''', (admin_user_id, 'supremo'))
                else:
                    cursor.execute('''
                        UPDATE administradores SET nivel = 'supremo', estado = 'activo'
                        WHERE usuario_id = ?
                    ''', (admin_user_id,))

            conn.commit()
            logger.info("✅ Base de datos inicializada correctamente")
            return True

    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
        return False

# --------------------------------------------------------------------------------------
# --- Funciones de Gestión de USUARIOS y ESTADOS (CRÍTICAS) ---
# --------------------------------------------------------------------------------------

def get_user_by_telegram_id(telegram_id):
    """Obtiene todos los datos del usuario por su telegram_id. (Resuelve el ImportError)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error obteniendo usuario por telegram_id {telegram_id}: {e}")
        return None

def get_user_internal_id(telegram_id):
    """Obtiene el ID interno (PRIMARY KEY) de la tabla 'usuarios'."""
    user_data = get_user_by_telegram_id(telegram_id)
    return user_data['id'] if user_data else None

def get_user_state(telegram_id):
    """Obtiene el estado actual de la FSM del usuario."""
    try:
        with get_db_connection() as conn:
            user = conn.execute("SELECT estado FROM usuarios WHERE telegram_id = ?", (telegram_id,)).fetchone()
            return user['estado'] if user else None
    except Exception as e:
        logger.error(f"Error obteniendo estado para {telegram_id}: {e}")
        return None

def set_user_state(telegram_id, state):
    """Establece el estado de la FSM del usuario."""
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE usuarios SET estado = ? WHERE telegram_id = ?", (state, telegram_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error estableciendo estado '{state}' para {telegram_id}: {e}")
        return False

def update_user_field(telegram_id, field, value):
    """Función genérica para actualizar un campo del usuario."""
    try:
        with get_db_connection() as conn:
            sql = f"UPDATE usuarios SET {field} = ? WHERE telegram_id = ?"
            conn.execute(sql, (value, telegram_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error actualizando campo '{field}' para {telegram_id}: {e}")
        return False
        
# --------------------------------------------------------------------------------------
# --- Funciones de GESTIÓN DE VEHÍCULOS (Vistas en snippets) ---
# --------------------------------------------------------------------------------------

def add_vehicle(telegram_id, tipo, placa, capacidad_toneladas):
    """Añade un vehículo a la tabla 'vehiculos'."""
    try:
        user_internal_id = get_user_internal_id(telegram_id)
        if not user_internal_id:
            return "error_user_not_found", None
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si la placa ya existe
            cursor.execute("SELECT id FROM vehiculos WHERE placa = ?", (placa,))
            if cursor.fetchone():
                return "error_plate_exists", None
            
            cursor.execute('''
                INSERT INTO vehiculos (usuario_id, tipo, placa, capacidad_toneladas, estado)
                VALUES (?, ?, ?, ?, 'activo')
            ''', (user_internal_id, tipo, placa, capacidad_toneladas))
            
            conn.commit()
            return "success", cursor.lastrowid
            
    except Exception as e:
        logger.error(f"Error añadiendo vehículo para {telegram_id}: {e}")
        return "error_db", None


# --------------------------------------------------------------------------------------
# --- Funciones de GESTIÓN DE SOLICITUDES (Vistas en snippets) ---
# --------------------------------------------------------------------------------------

def get_requests_for_transportista(telegram_id, limit=10):
    """
    Obtiene las solicitudes activas que coinciden con las zonas de trabajo
    y vehículos del transportista. (Lógica simplificada aquí).
    """
    try:
        user_db = get_user_by_telegram_id(telegram_id)
        if not user_db:
            return []
            
        # 1. Obtener las zonas de trabajo del transportista
        # Se asume que zonas_trabajo_ids es un JSON de IDs
        zonas_trabajo_ids = json.loads(user_db.get('zonas_trabajo_ids', '[]') or '[]')
        
        if not zonas_trabajo_ids:
            return [] # No tiene zonas configuradas
            
        # Para usar en la cláusula IN de SQL
        placeholders = ','.join('?' for _ in zonas_trabajo_ids)
            
        with get_db_connection() as conn:
            # Seleccionar solicitudes activas en las zonas de entrega del transportista
            sql_query = f'''
                SELECT s.*, u.nombre_completo as solicitante_nombre
                FROM solicitudes s
                JOIN usuarios u ON s.solicitante_id = u.id
                WHERE s.estado = 'pendiente'
                AND s.zona_entrega_id IN ({placeholders})
                AND s.solicitante_id != ? 
                ORDER BY s.creado_en DESC
                LIMIT ?
            '''
            params = zonas_trabajo_ids + [user_db['id'], limit]
            cursor = conn.execute(sql_query, params) 
            
            return cursor.fetchall()
            
    except Exception as e:
        logger.error(f"Error obteniendo solicitudes para transportista {telegram_id}: {e}")
        return []
