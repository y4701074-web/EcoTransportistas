import sqlite3
import json 
from config import logger, ADMIN_SUPREMO, ADMIN_SUPREMO_ID # ADMIN_SUPREMO_ID es crítico aquí
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

            # TABLAS GEOGRÁFICAS, SOLICITUDES, VEHÍCULOS, AUDITORÍA (Se omiten por brevedad, asumiendo que son correctas)
            # ... (Las definiciones de las tablas paises, provincias, zonas, solicitudes, vehiculos, auditoria se mantienen aquí)
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
            
            # 1. Insertar/Actualizar al Admin Supremo en la tabla de usuarios (usando OR IGNORE para manejar duplicados)
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, estado)
                VALUES (?, ?, ?, ?, ?, 'activo')
            ''', (ADMIN_SUPREMO_ID, ADMIN_SUPREMO, "Admin Supremo", "N/A", "ambos"))
            
            # Obtener el ID interno del usuario supremo (siempre se hará después de la inserción)
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (ADMIN_SUPREMO_ID,))
            admin_user_id = cursor.fetchone()[0]

            # 2. Asegurar que el Admin Supremo tenga rol 'supremo' en la tabla `administradores`
            # Usamos una inserción o reemplazo para asegurar que el nivel sea 'supremo'
            cursor.execute("SELECT usuario_id FROM administradores WHERE usuario_id = ?", (admin_user_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO administradores (usuario_id, nivel, estado)
                    VALUES (?, ?, 'activo')
                ''', (admin_user_id, 'supremo'))
            else:
                 # Actualizar por si acaso ya existía con un nivel inferior (e.g., por error)
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

def get_user_language(user_id):
    # Se utiliza la nueva conexión
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT idioma FROM usuarios WHERE telegram_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 'es'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'es'

def log_audit(accion, user_id, detalles=""):
    # Se utiliza la nueva conexión
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO auditoria (accion, usuario_id, detalles)
                VALUES (?, ?, ?)
            ''', (accion, user_id, detalles))
            conn.commit()
    except Exception as e:
        logger.error(f"Error en auditoría: {e}")

def get_user_by_telegram_id(user_id):
    """
    Obtiene todos los datos del usuario por su ID de Telegram.
    NOTA: Se mejoró el manejo de JSON para 'zonas_trabajo_ids'.
    """
    try:
        with get_db_connection() as conn:
            # conn.row_factory ya está configurado en get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (user_id,))
            user_data = cursor.fetchone()

            if user_data:
                # Convertimos la fila a diccionario para poder modificarla
                data = dict(user_data) 
                
                # Manejo robusto de la columna JSON
                json_string = data.get('zonas_trabajo_ids')
                if json_string:
                    try:
                        data['zonas_trabajo_ids'] = json.loads(json_string)
                    except json.JSONDecodeError:
                        logger.warning(f"Error de parseo JSON para zonas_trabajo_ids del usuario {user_id}. Se devuelve lista vacía.")
                        data['zonas_trabajo_ids'] = []
                else:
                    data['zonas_trabajo_ids'] = []

                return data

            return None # Devolver None si el usuario no existe

    except Exception as e:
        logger.error(f"Error obteniendo datos de usuario {user_id}: {e}")
        return None

def set_user_registration_data(telegram_id, username, name, phone, user_type, pais_id, provincia_id, zona_id, lang='es'):
    # Se utiliza la nueva conexión
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Buscar si el usuario ya existe
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (telegram_id,))
            existing_user = cursor.fetchone()

            if existing_user:
                # Si existe, actualizamos
                cursor.execute('''
                    UPDATE usuarios SET username = ?, nombre_completo = ?, telefono = ?, tipo = ?, 
                    pais_id = ?, provincia_id = ?, zona_id = ?, idioma = ?, estado = 'activo'
                    WHERE telegram_id = ?
                ''', (username, name, phone, user_type, pais_id, provincia_id, zona_id, lang, telegram_id))
            else:
                # Si no existe, insertamos
                cursor.execute('''
                    INSERT INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, pais_id, provincia_id, zona_id, idioma, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'activo')
                ''', (telegram_id, username, name, phone, user_type, pais_id, provincia_id, zona_id, lang))

            conn.commit()
            return True

    except Exception as e:
        logger.error(f"Error guardando datos de registro para {telegram_id}: {e}")
        return False

def get_user_internal_id(telegram_id):
    # Se utiliza la nueva conexión
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error obteniendo ID interno para {telegram_id}: {e}")
        return None

def get_admin_data(telegram_id):
    """
    Obtiene el nivel y región de un administrador por su ID de Telegram.
    
    🔑 CORRECCIÓN CRÍTICA: Prioriza el ADMIN_SUPREMO_ID de la variable de entorno
    para asegurar que su nivel siempre sea 'supremo', anulando la BD.
    """
    try:
        # 🚨 LÓGICA DE ADMINISTRADOR SUPREMO (PRIORIDAD AL ID DE ENTORNO) 🚨
        if str(telegram_id) == str(ADMIN_SUPREMO_ID):
            # Crea un objeto Row simulado con nivel 'supremo' y devuelve los datos
            # Esto garantiza que el nivel 'supremo' siempre se respete, sin importar lo que diga la tabla
            admin_data = {
                'id': 0, # ID ficticio o puedes buscar el real si lo necesitas, pero el nivel es la clave
                'usuario_id': get_user_internal_id(telegram_id), # Asegura el ID interno
                'nivel': 'supremo',
                'pais_id': None, 
                'provincia_id': None,
                'zona_id': None,
                'comision_transportistas': 100.0,
                'comision_solicitantes': 50.0,
                'porcentaje_minimo_ganancia': 5.0,
                'estado': 'activo',
                'creado_en': None # No es necesario para el control de acceso
            }
            # Se utiliza el constructor de Row para simular un resultado de DB
            return sqlite3.Row(list(admin_data.keys()), list(admin_data.values()))


        # Si no es el admin supremo, consulta la tabla normalmente
        with get_db_connection() as conn:
            # conn.row_factory ya está configurado para devolver Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*
                FROM administradores a
                JOIN usuarios u ON a.usuario_id = u.id
                WHERE u.telegram_id = ? AND a.estado = 'activo'
            ''', (telegram_id,))
            return cursor.fetchone()

    except Exception as e:
        logger.error(f"Error obteniendo datos de admin para {telegram_id}: {e}")
        return None

def set_user_work_zones(telegram_id, zonas_trabajo_ids):
    # Se utiliza la nueva conexión
    try:
        # Convertir la lista de IDs a una cadena JSON
        zonas_json = json.dumps(zonas_trabajo_ids)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios 
                SET zonas_trabajo_ids = ?
                WHERE telegram_id = ?
            ''', (zonas_json, telegram_id))
            conn.commit()
            return True

    except Exception as e:
        logger.error(f"Error guardando zonas de trabajo para {telegram_id}: {e}")
        return False

def get_requests_for_transportista(user_db, limit=10):
    # Se utiliza la nueva conexión
    try:
        # 1. Obtener las zonas de trabajo del usuario (ya es una lista gracias a get_user_by_telegram_id)
        zonas_trabajo = user_db.get('zonas_trabajo_ids', [])

        if not zonas_trabajo:
            return []

        # 2. Crear un string de placeholders (?, ?, ?, ...) para la cláusula IN
        placeholders = ','.join(['?'] * len(zonas_trabajo))

        with get_db_connection() as conn:
            # conn.row_factory ya está configurado para devolver Row
            cursor = conn.cursor()

            # La consulta filtra por: estado 'activa', zona_id coincidente, y no ser el propio solicitante.
            cursor.execute(f'''
                SELECT s.*, u.nombre_completo AS solicitante_nombre
                FROM solicitudes s
                JOIN usuarios u ON s.usuario_id = u.id
                WHERE s.estado = 'activa' 
                AND s.zona_id IN ({placeholders})
                AND s.usuario_id != ?
                ORDER BY s.creado_en DESC
                LIMIT ?
            ''', zonas_trabajo + [user_db['id'], limit]) # Añadir el ID interno del usuario y el límite

            return cursor.fetchall()

    except Exception as e:
        logger.error(f"Error obteniendo solicitudes para transportista {user_db['telegram_id']}: {e}")
        return []


def add_vehicle(user_id, tipo, placa, capacidad_toneladas):
    # Se utiliza la nueva conexión
    try:
        user_internal_id = get_user_internal_id(user_id)
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
        logger.error(f"Error añadiendo vehículo para {user_id}: {e}")
        return "error_db", None
