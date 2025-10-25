# db.py
import sqlite3
import json
from config import logger, ADMIN_SUPREMO, ADMIN_SUPREMO_ID

DATABASE_FILE = 'ecotransportistas.db'

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
        return None

def init_db():
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ No se pudo conectar a la base de datos")
            return False
            
        cursor = conn.cursor()

        # --- 1. CREACIÓN DE TABLAS ---

        # TABLA DE USUARIOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                nombre_completo TEXT,
                telefono TEXT,
                tipo TEXT,
                
                -- Nuevas columnas de ID para geografía de residencia
                pais_id INTEGER,
                provincia_id INTEGER,
                zona_id INTEGER,
                
                idioma TEXT DEFAULT 'es',
                estado TEXT DEFAULT 'activo',
                vehiculos TEXT DEFAULT '[]',
                
                -- Nueva columna para filtros de zona de trabajo del transportista
                zonas_trabajo_ids TEXT DEFAULT '[]', 
                
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # TABLA DE ADMINISTRADORES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                nivel TEXT,
                
                -- Nuevas columnas de ID para jurisdicción
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
        
        # TABLAS GEOGRÁFICAS
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

        # TABLA DE SOLICITUDES
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
        
        # TABLA DE VEHÍCULOS
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

        # TABLA DE AUDITORÍA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion TEXT,
                usuario_id INTEGER,
                detalles TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # --- 2. INSERCIÓN DEL ADMINISTRADOR SUPREMO ---
        # 1. Asegurar que el Admin Supremo esté registrado en la tabla `usuarios`
        cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (ADMIN_SUPREMO_ID,))
        admin_user_id = cursor.fetchone()
        
        if not admin_user_id:
            # Insertar al admin supremo en la tabla de usuarios
            cursor.execute('''
                INSERT INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, pais_id, provincia_id, zona_id, estado)
                VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, 'activo')
            ''', (ADMIN_SUPREMO_ID, ADMIN_SUPREMO, "Admin Supremo", "N/A", "ambos"))
            admin_user_id = cursor.lastrowid
            logger.info(f"✅ Admin Supremo insertado en usuarios con ID: {admin_user_id}")
        else:
            admin_user_id = admin_user_id[0]
            
        # 2. Asegurar que el Admin Supremo tenga rol en la tabla `administradores`
        cursor.execute("SELECT nivel FROM administradores WHERE usuario_id = ? AND estado = 'activo'", (admin_user_id,))
        admin_role = cursor.fetchone()
        
        if not admin_role:
            cursor.execute('''
                INSERT INTO administradores (usuario_id, nivel, pais_id, provincia_id, zona_id, estado)
                VALUES (?, ?, NULL, NULL, NULL, 'activo')
            ''', (admin_user_id, 'supremo'))
            logger.info("✅ Rol de Admin Supremo asignado en administradores")
            
        # --- 3. FINALIZACIÓN ---
        conn.commit()
        conn.close()
        logger.info("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
        return False

# --- Helper functions para DB ---

def get_user_language(user_id):
    try:
        conn = get_db_connection()
        if not conn:
            return 'es'
            
        cursor = conn.cursor()
        cursor.execute("SELECT idioma FROM usuarios WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'es'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'es'

def log_audit(accion, user_id, detalles=""):
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO auditoria (accion, usuario_id, detalles)
            VALUES (?, ?, ?)
        ''', (accion, user_id, detalles))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error en auditoría: {e}")

def get_user_by_telegram_id(user_id):
    """Obtiene todos los datos del usuario por su ID de Telegram, incluyendo la conversión de JSON de las zonas de trabajo."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            return None
            
        # Convertir a diccionario para poder modificar
        user_dict = dict(user_data)
        
        # Convertir zonas_trabajo_ids de JSON string a lista de enteros
        if user_dict.get('zonas_trabajo_ids'):
            try:
                user_dict['zonas_trabajo_ids'] = json.loads(user_dict['zonas_trabajo_ids'])
            except:
                user_dict['zonas_trabajo_ids'] = []
        else:
            user_dict['zonas_trabajo_ids'] = []
            
        return user_dict
            
    except Exception as e:
        logger.error(f"Error obteniendo datos de usuario {user_id}: {e}")
        return None

def set_user_registration_data(telegram_id, username, name, phone, user_type, pais_id, provincia_id, zona_id, lang='es'):
    """Actualiza o inserta los datos de registro de un usuario, usando IDs geográficos."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
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
            logger.info(f"✅ Usuario {telegram_id} actualizado en la base de datos")
        else:
            # Si no existe, insertamos
            cursor.execute('''
                INSERT INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, pais_id, provincia_id, zona_id, idioma, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'activo')
            ''', (telegram_id, username, name, phone, user_type, pais_id, provincia_id, zona_id, lang))
            logger.info(f"✅ Nuevo usuario {telegram_id} insertado en la base de datos")
            
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error guardando datos de registro para {telegram_id}: {e}")
        return False
        
def get_user_internal_id(telegram_id):
    """Obtiene el ID interno (AUTOINCREMENT) del usuario."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error obteniendo ID interno para {telegram_id}: {e}")
        return None
        
def get_admin_data(telegram_id):
    """Obtiene el nivel y región de un administrador por su ID de Telegram."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.nivel, a.pais_id, a.provincia_id, a.zona_id
            FROM administradores a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE u.telegram_id = ? AND a.estado = 'activo'
        ''', (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'nivel': result[0],
                'pais_id': result[1],
                'provincia_id': result[2],
                'zona_id': result[3]
            }
        return None
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de admin para {telegram_id}: {e}")
        return None

def set_user_work_zones(telegram_id, zonas_trabajo_ids):
    """
    Guarda la lista de IDs de zona de trabajo para un transportista.
    zonas_trabajo_ids debe ser una lista de enteros.
    """
    try:
        # Convertir la lista de IDs a una cadena JSON
        zonas_json = json.dumps(zonas_trabajo_ids)
        
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE usuarios 
            SET zonas_trabajo_ids = ?
            WHERE telegram_id = ?
        ''', (zonas_json, telegram_id))
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error guardando zonas de trabajo para {telegram_id}: {e}")
        return False

def get_requests_for_transportista(user_db, limit=10):
    """
    Obtiene solicitudes activas que coinciden con las zonas de trabajo del transportista.
    """
    try:
        # 1. Obtener las zonas de trabajo del usuario
        zonas_trabajo = user_db.get('zonas_trabajo_ids', [])
        
        # Si el usuario no tiene zonas definidas, no hay solicitudes para mostrar
        if not zonas_trabajo:
            return []
            
        conn = get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        # 2. Crear un string de placeholders para la cláusula IN
        placeholders = ','.join(['?'] * len(zonas_trabajo))
        
        # La consulta filtra por estado 'activa' y zonas de trabajo
        query = f'''
            SELECT s.*, u.nombre_completo AS solicitante_nombre
            FROM solicitudes s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.estado = 'activa' 
            AND s.zona_id IN ({placeholders})
            AND s.usuario_id != ?
            ORDER BY s.creado_en DESC
            LIMIT ?
        '''
        
        params = zonas_trabajo + [user_db['id'], limit]
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return results
            
    except Exception as e:
        logger.error(f"Error obteniendo solicitudes para transportista {user_db.get('telegram_id', 'unknown')}: {e}")
        return []

def add_vehicle(user_id, tipo, placa, capacidad_toneladas):
    """Añade un vehículo a la tabla 'vehiculos'."""
    try:
        user_internal_id = get_user_internal_id(user_id)
        if not user_internal_id:
            return "error_user_not_found", None
            
        conn = get_db_connection()
        if not conn:
            return "error_db", None
            
        cursor = conn.cursor()
        
        # Verificar si la placa ya existe
        cursor.execute("SELECT id FROM vehiculos WHERE placa = ?", (placa,))
        if cursor.fetchone():
            conn.close()
            return "error_plate_exists", None
        
        cursor.execute('''
            INSERT INTO vehiculos (usuario_id, tipo, placa, capacidad_toneladas, estado)
            VALUES (?, ?, ?, ?, 'activo')
        ''', (user_internal_id, tipo, placa, capacidad_toneladas))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return "success", new_id
        
    except Exception as e:
        logger.error(f"Error añadiendo vehículo para {user_id}: {e}")
        return "error_db", None

# Nueva función crítica para registro.py
def get_user_state(telegram_id):
    """Obtiene el estado actual del usuario por su Telegram ID."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("SELECT estado FROM usuarios WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error obteniendo estado del usuario {telegram_id}: {e}")
        return None

def set_user_state(telegram_id, state):
    """Actualiza el estado del usuario por su Telegram ID."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET estado = ? WHERE telegram_id = ?", (state, telegram_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error actualizando estado del usuario {telegram_id}: {e}")
        return False