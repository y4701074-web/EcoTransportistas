import sqlite3
from config import logger, ADMIN_SUPREMO_ID
# Se elimina la importación de ADMIN_SUPREMO (string) y se usa ADMIN_SUPREMO_ID (int)

DATABASE_FILE = 'ecotransportistas.db'

def init_db():
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # --- TABLAS DE ESTRUCTURA GEOGRÁFICA (NUEVAS) ---
            
            # 1. Tabla PAISES
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    codigo TEXT UNIQUE NOT NULL,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    FOREIGN KEY (creado_por_admin_id) REFERENCES usuarios(id)
                )
            ''')

            # 2. Tabla PROVINCIAS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS provincias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pais_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    UNIQUE(pais_id, nombre),
                    FOREIGN KEY (pais_id) REFERENCES paises(id),
                    FOREIGN KEY (creado_por_admin_id) REFERENCES usuarios(id)
                )
            ''')
            
            # 3. Tabla ZONAS (o municipios/distritos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS zonas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provincia_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    UNIQUE(provincia_id, nombre),
                    FOREIGN KEY (provincia_id) REFERENCES provincias(id),
                    FOREIGN KEY (creado_por_admin_id) REFERENCES usuarios(id)
                )
            ''')
            
            # --- TABLAS PRINCIPALES (MODIFICACIONES) ---

            # 4. Tabla de usuarios (MODIFICADA)
            # Ahora usa IDs de la tabla geográfica
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    nombre_completo TEXT,
                    telefono TEXT,
                    tipo TEXT, 
                    pais_id INTEGER,
                    provincia_id INTEGER,
                    zona_id INTEGER,
                    capacidad_carga REAL DEFAULT 0.0, -- NUEVO: Capacidad máxima en toneladas o unidad relevante
                    idioma TEXT DEFAULT 'es',
                    estado TEXT DEFAULT 'activo',
                    -- vehiculos TEXT DEFAULT '[]', -- Esto se podría mover a una tabla separada 'vehiculos_transportista' si crece
                    zonas_trabajo_ids TEXT DEFAULT '[]', -- Array JSON de IDs de ZONAS
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (pais_id) REFERENCES paises(id),
                    FOREIGN KEY (provincia_id) REFERENCES provincias(id),
                    FOREIGN KEY (zona_id) REFERENCES zonas(id)
                )
            ''')
            
            # 5. Tabla de administradores (MODIFICADA)
            # Se ajusta la columna region_asignada y el nivel
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS administradores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER UNIQUE NOT NULL,
                    nivel TEXT NOT NULL, -- 'supremo', 'supremo_2', 'pais', 'provincia', 'zona'
                    pais_id INTEGER NULL,
                    provincia_id INTEGER NULL,
                    zona_id INTEGER NULL,
                    creado_por_admin_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (pais_id) REFERENCES paises(id),
                    FOREIGN KEY (provincia_id) REFERENCES provincias(id),
                    FOREIGN KEY (zona_id) REFERENCES zonas(id),
                    FOREIGN KEY (creado_por_admin_id) REFERENCES usuarios(id)
                )
            ''')
            
            # 6. Tabla de solicitudes (MODIFICADA)
            # Ahora usa IDs de la tabla geográfica
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS solicitudes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    pais_id INTEGER NOT NULL,
                    provincia_id INTEGER NOT NULL,
                    zona_id INTEGER,
                    vehiculo_tipo TEXT,
                    carga_tipo TEXT,
                    descripcion TEXT,
                    direccion_recogida TEXT NOT NULL,
                    direccion_entrega TEXT NOT NULL,
                    puntos_referencia TEXT,
                    presupuesto REAL,
                    estado TEXT DEFAULT 'activa', -- activa, pendiente_confirmacion, completada, cancelada
                    transportista_asignado INTEGER,
                    pending_confirm_until TIMESTAMP,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (pais_id) REFERENCES paises(id),
                    FOREIGN KEY (provincia_id) REFERENCES provincias(id),
                    FOREIGN KEY (zona_id) REFERENCES zonas(id),
                    FOREIGN KEY (transportista_asignado) REFERENCES usuarios(id)
                )
            ''')
            
            # 7. Tabla de auditoría (MANTENIDA)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accion TEXT NOT NULL,
                    usuario_id INTEGER,
                    detalles TEXT,
                    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- LÓGICA DE INYECCIÓN DE ADMIN SUPREMO ---
            # Asegurar que el Admin Supremo esté en la tabla de usuarios y administradores
            
            # Insertar/Actualizar usuario Admin Supremo
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (ADMIN_SUPREMO_ID,))
            admin_user = cursor.fetchone()
            
            if not admin_user:
                # Si no existe como usuario, insertarlo
                cursor.execute('''
                    INSERT INTO usuarios (telegram_id, nombre_completo, telefono, tipo, estado)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ADMIN_SUPREMO_ID, "Admin Supremo", "N/A", "ambos", "activo"))
                admin_user_id = cursor.lastrowid
            else:
                admin_user_id = admin_user[0]
                # Asegurarse de que el tipo y el nombre sean correctos
                cursor.execute('''
                    UPDATE usuarios SET nombre_completo = ?, tipo = ?, estado = ? WHERE id = ?
                ''', ("Admin Supremo", "ambos", "activo", admin_user_id))

            # Insertar/Actualizar rol de administrador supremo
            cursor.execute("SELECT nivel FROM administradores WHERE usuario_id = ?", (admin_user_id,))
            admin_role = cursor.fetchone()
            
            if not admin_role:
                # Si no tiene rol de admin, asignárselo
                cursor.execute('''
                    INSERT INTO administradores (usuario_id, nivel, estado)
                    VALUES (?, ?, ?)
                ''', (admin_user_id, "supremo", "activo"))
            elif admin_role[0] != "supremo":
                 # Si tiene un rol diferente, actualizarlo a supremo
                 cursor.execute('''
                    UPDATE administradores SET nivel = ?, estado = ? WHERE usuario_id = ?
                ''', ("supremo", "activo", admin_user_id))
            
            conn.commit()
            logger.info("✅ Base de datos inicializada correctamente y Admin Supremo asegurado")
            return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")
        return False

# --- Helper functions para DB (MODIFICADAS) ---

def get_user_language(user_id):
    # Se mantiene la misma lógica para el idioma
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
    # Se mantiene la misma lógica para la auditoría
    try:
        # Nota: Aquí user_id es el telegram_id, pero la tabla auditoria usa el id interno.
        # Por simplicidad, por ahora usamos el telegram_id, pero lo ideal sería buscar el id interno.
        # Para que funcione con la tabla actual, asumimos que 'usuario_id' en auditoria es el telegram_id
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
    # Se mantiene la misma lógica, usando Row para acceso por nombre
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error obteniendo usuario por telegram_id: {e}")
        return None

def get_admin_data(user_id):
    """Obtiene el nivel de administración y las IDs geográficas asignadas."""
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Buscar el ID interno del usuario
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (user_id,))
            user_internal_id = cursor.fetchone()
            if not user_internal_id:
                return None
            
            # Buscar los datos del administrador
            cursor.execute('''
                SELECT a.nivel, a.pais_id, a.provincia_id, a.zona_id
                FROM administradores a
                WHERE a.usuario_id = ? AND a.estado = 'activo'
            ''', (user_internal_id['id'],))
            
            return cursor.fetchone()
            
    except Exception as e:
        logger.error(f"Error obteniendo datos de administrador: {e}")
        return None
        
def get_user_internal_id(telegram_id):
    """Obtiene el ID interno (AUTOINCREMENT) de la tabla usuarios."""
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error obteniendo ID interno: {e}")
        return None
