import sqlite3
from config import logger, ADMIN_SUPREMO

DATABASE_FILE = 'ecotransportistas.db'

def init_db():
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Tabla de usuarios COMPLETA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    nombre_completo TEXT,
                    telefono TEXT,
                    tipo TEXT,
                    pais TEXT DEFAULT 'Cuba',
                    provincia TEXT,
                    zona TEXT,
                    idioma TEXT DEFAULT 'es',
                    estado TEXT DEFAULT 'activo',
                    vehiculos TEXT DEFAULT '[]',
                    zonas_trabajo TEXT DEFAULT '[]',
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de administradores COMPLETA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS administradores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER UNIQUE,
                    nivel TEXT,
                    region_asignada TEXT,
                    comision_transportistas REAL DEFAULT 100,
                    comision_solicitantes REAL DEFAULT 50,
                    porcentaje_superior REAL DEFAULT 20,
                    estado TEXT DEFAULT 'activo',
                    cuenta_bancaria TEXT,
                    designado_por TEXT,
                    fecha_designacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            ''')
            
            # Tabla de solicitudes COMPLETA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solicitudes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    tipo_vehiculo TEXT,
                    tipo_carga TEXT,
                    descripcion TEXT,
                    peso TEXT,
                    direccion_desde TEXT,
                    direccion_hacia TEXT,
                    presupuesto REAL,
                    estado TEXT DEFAULT 'activa',
                    transportista_asignado INTEGER,
                    pending_confirm_until TIMESTAMP,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                    FOREIGN KEY (transportista_asignado) REFERENCES usuarios (id)
                )
            ''')
            
            # Tabla de auditoría
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accion TEXT,
                    usuario_id INTEGER,
                    detalles TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insertar admin supremo si no existe
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (ADMIN_SUPREMO,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, provincia, zona, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ADMIN_SUPREMO, ADMIN_SUPREMO, "Administrador Supremo", "N/A", "admin_supremo", "Todas", "Todas", "activo"))
                
                cursor.execute('''
                    INSERT INTO administradores (usuario_id, nivel, region_asignada, comision_transportistas, comision_solicitantes, porcentaje_superior)
                    VALUES ((SELECT id FROM usuarios WHERE telegram_id = ?), 'supremo', 'Todo Cuba', 0, 0, 0)
                ''', (ADMIN_SUPREMO,))
            
            conn.commit()
        logger.info("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
        return False

# --- Helper functions para DB ---

def get_user_language(user_id):
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT idioma FROM usuarios WHERE telegram_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 'es'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'es'

def log_audit(accion, user_id, detalles=""):
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO auditoria (accion, usuario_id, detalles)
                VALUES (?, ?, ?)
            ''', (accion, user_id, detalles))
            conn.commit()
    except Exception as e:
        logger.error(f"Error en auditoría: {e}")

def get_user_by_telegram_id(user_id):
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting user by telegram_id: {e}")
        return None
          
