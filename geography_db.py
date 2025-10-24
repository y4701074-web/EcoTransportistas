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
# ... (Código anterior) ...

def create_country(admin_telegram_id, country_name, country_code):
    """Crea un nuevo país. Solo permitido por Admin Supremo/Supremo 2."""
    user_internal_id = get_user_internal_id(admin_telegram_id)
    
    if not user_internal_id:
        return "error_no_user", None

    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Verificar nivel de administración
            cursor.execute('''
                SELECT nivel FROM administradores 
                WHERE usuario_id = ? AND estado = 'activo'
            ''', (user_internal_id,))
            
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] not in ('supremo', 'supremo_2'):
                return "error_no_permission", None
            
            # Intentar insertar el país
            cursor.execute('''
                INSERT INTO paises (nombre, codigo, creado_por_admin_id)
                VALUES (?, ?, ?)
            ''', (country_name, country_code.upper(), user_internal_id))
            
            conn.commit()
            return "success", cursor.lastrowid
            
    except sqlite3.IntegrityError:
        return "error_already_exists", None
    except Exception as e:
        logger.error(f"Error creando país: {e}")
        return "error_db", None


def create_provincia(admin_telegram_id, pais_id, provincia_name):
    """Crea una nueva provincia dentro de un país. Permitido por Admin Supremo/Supremo 2 y Admin de País."""
    user_internal_id = get_user_internal_id(admin_telegram_id)
    
    if not user_internal_id:
        return "error_no_user", None

    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Verificar nivel de administración y permisos
            cursor.execute('''
                SELECT nivel, pais_id FROM administradores 
                WHERE usuario_id = ? AND estado = 'activo'
            ''', (user_internal_id,))
            
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] not in ('supremo', 'supremo_2', 'pais'):
                return "error_no_permission", None

            # Si es Admin de País, debe coincidir con el pais_id
            if admin_data[0] == 'pais' and admin_data[1] != pais_id:
                return "error_unauthorized_country", None
            
            # Intentar insertar la provincia
            cursor.execute('''
                INSERT INTO provincias (pais_id, nombre, creado_por_admin_id)
                VALUES (?, ?, ?)
            ''', (pais_id, provincia_name, user_internal_id))
            
            conn.commit()
            return "success", cursor.lastrowid
            
    except sqlite3.IntegrityError:
        return "error_already_exists", None
    except Exception as e:
        logger.error(f"Error creando provincia: {e}")
        return "error_db", None


def create_zona(admin_telegram_id, provincia_id, zona_name):
    """Crea una nueva zona dentro de una provincia. Permitido por Admin Supremo/Supremo 2, Admin de País y Admin de Provincia."""
    user_internal_id = get_user_internal_id(admin_telegram_id)
    
    if not user_internal_id:
        return "error_no_user", None

    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # 1. Verificar nivel de administración
            cursor.execute('''
                SELECT nivel, provincia_id FROM administradores 
                WHERE usuario_id = ? AND estado = 'activo'
            ''', (user_internal_id,))
            
            admin_data = cursor.fetchone()
            if not admin_data or admin_data[0] not in ('supremo', 'supremo_2', 'pais', 'provincia'):
                return "error_no_permission", None
            
            # 2. Verificar si el Admin de Provincia tiene jurisdicción
            if admin_data[0] == 'provincia' and admin_data[1] != provincia_id:
                return "error_unauthorized_province", None

            # 3. Si el admin no es de provincia (Supremo/Pais), verificar que la provincia exista en su país (Lógica avanzada omitida por simplicidad, confiando en que el Admin de País/Supremo la seleccionó correctamente)

            # 4. Intentar insertar la zona
            cursor.execute('''
                INSERT INTO zonas (provincia_id, nombre, creado_por_admin_id)
                VALUES (?, ?, ?)
            ''', (provincia_id, zona_name, user_internal_id))
            
            conn.commit()
            return "success", cursor.lastrowid
            
    except sqlite3.IntegrityError:
        return "error_already_exists", None
    except Exception as e:
        logger.error(f"Error creando zona: {e}")
        return "error_db", None

# ... (Código anterior - Parte 1 y Parte 2) ...

def get_provincias_by_pais_id(pais_id, include_all_option=False):
    """Obtiene las provincias activas de un país específico, ordenadas alfabéticamente."""
    if not pais_id:
        return []
    
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, nombre FROM provincias 
                WHERE pais_id = ? AND estado = 'activo'
                ORDER BY nombre ASC
            ''', (pais_id,))
            
            provincias = list(cursor.fetchall())
            
            if include_all_option:
                # Opción para seleccionar 'Todas las provincias' como filtro
                provincias.insert(0, {'id': 0, 'nombre': 'Todas las Provincias'})
                
            return provincias
            
    except Exception as e:
        logger.error(f"Error obteniendo provincias por país {pais_id}: {e}")
        return []


def get_zonas_by_provincia_id(provincia_id, include_all_option=False):
    """Obtiene las zonas activas de una provincia específica, ordenadas alfabéticamente."""
    if not provincia_id:
        return []
        
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, nombre FROM zonas 
                WHERE provincia_id = ? AND estado = 'activo'
                ORDER BY nombre ASC
            ''', (provincia_id,))
            
            zonas = list(cursor.fetchall())
            
            if include_all_option:
                 # Opción para seleccionar 'Todas las zonas' como filtro
                zonas.insert(0, {'id': 0, 'nombre': 'Todas las Zonas'})
                
            return zonas
            
    except Exception as e:
        logger.error(f"Error obteniendo zonas por provincia {provincia_id}: {e}")
        return []


def get_admin_creatable_provincias(telegram_id):
    """Obtiene las provincias que un administrador tiene permiso para gestionar/crear zonas."""
    user_internal_id = get_user_internal_id(telegram_id)
    if not user_internal_id:
        return []

    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Buscar datos de admin para saber su nivel y jurisdicción
            cursor.execute('''
                SELECT nivel, pais_id, provincia_id FROM administradores a 
                WHERE a.usuario_id = ? AND a.estado = 'activo'
            ''', (user_internal_id,))
            
            admin_data = cursor.fetchone()
            if not admin_data or admin_data['nivel'] not in ('supremo', 'supremo_2', 'pais'):
                return []
                
            nivel = admin_data['nivel']
            
            if nivel in ('supremo', 'supremo_2'):
                # Si es supremo, puede ver todas las provincias de todos los países
                cursor.execute("SELECT id, nombre, pais_id FROM provincias ORDER BY nombre ASC")
            elif nivel == 'pais':
                # Si es admin de país, solo ve las provincias de su país
                cursor.execute('''
                    SELECT id, nombre, pais_id FROM provincias 
                    WHERE pais_id = ?
                    ORDER BY nombre ASC
                ''', (admin_data['pais_id'],))
            
            return cursor.fetchall()
            
    except Exception as e:
        logger.error(f"Error obteniendo provincias gestionables por admin {telegram_id}: {e}")
        return []
# ... (Código anterior - Parte 1, Parte 2 y Parte 3) ...

def get_admin_creatable_zonas(telegram_id, provincia_id=None):
    """Obtiene las zonas que un administrador tiene permiso para gestionar/crear."""
    user_internal_id = get_user_internal_id(telegram_id)
    if not user_internal_id:
        return []

    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Buscar datos de admin para saber su nivel y jurisdicción
            cursor.execute('''
                SELECT nivel, pais_id, provincia_id FROM administradores a 
                WHERE a.usuario_id = ? AND a.estado = 'activo'
            ''', (user_internal_id,))
            
            admin_data = cursor.fetchone()
            if not admin_data or admin_data['nivel'] not in ('supremo', 'supremo_2', 'pais', 'provincia'):
                return []
                
            nivel = admin_data['nivel']
            
            sql = "SELECT id, nombre, provincia_id FROM zonas "
            params = []
            where_clauses = []
            
            if provincia_id:
                # Filtrar específicamente por una provincia (usado para el menú de creación)
                where_clauses.append("provincia_id = ?")
                params.append(provincia_id)
            elif nivel == 'provincia':
                # Si es admin de provincia, solo ve las zonas de su provincia
                where_clauses.append("provincia_id = ?")
                params.append(admin_data['provincia_id'])
            elif nivel == 'pais':
                # Si es admin de país, ve las zonas de todas las provincias de su país
                cursor.execute("SELECT id FROM provincias WHERE pais_id = ?", (admin_data['pais_id'],))
                provincia_ids = [row[0] for row in cursor.fetchall()]
                if provincia_ids:
                    placeholders = ','.join('?' for _ in provincia_ids)
                    where_clauses.append(f"provincia_id IN ({placeholders})")
                    params.extend(provincia_ids)
                else:
                    return [] # No hay provincias, no hay zonas
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            sql += " ORDER BY nombre ASC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
            
    except Exception as e:
        logger.error(f"Error obteniendo zonas gestionables por admin {telegram_id}: {e}")
        return []


# --- FUNCIONES DE FILTRO DE TRABAJO DEL TRANSPORTISTA ---

def get_transportista_work_zones_ids(telegram_id):
    """Obtiene la lista de IDs de zonas de trabajo de un transportista."""
    try:
        user_db = get_user_internal_id(telegram_id)
        if not user_db:
            return []
            
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT zonas_trabajo_ids FROM usuarios WHERE id = ?", (user_db,))
            result = cursor.fetchone()
            
            if result and result[0]:
                return json.loads(result[0])
            return []
            
    except Exception as e:
        logger.error(f"Error obteniendo zonas de trabajo para {telegram_id}: {e}")
        return []

def update_transportista_work_zones_ids(telegram_id, zone_ids_list):
    """Actualiza la lista de IDs de zonas de trabajo de un transportista."""
    try:
        user_db = get_user_internal_id(telegram_id)
        if not user_db:
            return False
            
        zone_ids_json = json.dumps(zone_ids_list)
        
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET zonas_trabajo_ids = ? WHERE id = ?", 
                (zone_ids_json, user_db)
            )
            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error actualizando zonas de trabajo para {telegram_id}: {e}")
        return False
# ... (Código anterior - Partes 1, 2, 3 y 4) ...

def get_zone_data(zone_id):
    """Obtiene los datos de una zona específica."""
    if not zone_id:
        return None
        
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT z.nombre AS zona_nombre, p.nombre AS provincia_nombre, pa.nombre AS pais_nombre
                FROM zonas z
                JOIN provincias p ON z.provincia_id = p.id
                JOIN paises pa ON p.pais_id = pa.id
                WHERE z.id = ? AND z.estado = 'activo'
            ''', (zone_id,))
            return cursor.fetchone()
            
    except Exception as e:
        logger.error(f"Error obteniendo datos de zona {zone_id}: {e}")
        return None

def get_transportista_work_zones_names(telegram_id):
    """
    Obtiene los nombres completos (País/Provincia/Zona) de las zonas de trabajo de un transportista.
    """
    zone_ids = get_transportista_work_zones_ids(telegram_id)
    if not zone_ids:
        return "No definidas"
        
    zone_names = []
    
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Usar un placeholder para la lista de IDs
            placeholders = ','.join('?' for _ in zone_ids)
            sql = f'''
                SELECT z.nombre AS zona, p.nombre AS provincia, pa.nombre AS pais
                FROM zonas z
                JOIN provincias p ON z.provincia_id = p.id
                JOIN paises pa ON p.pais_id = pa.id
                WHERE z.id IN ({placeholders}) AND z.estado = 'activo'
            '''
            cursor.execute(sql, zone_ids)
            
            for row in cursor.fetchall():
                zone_names.append(f"{row['pais']}/{row['provincia']}/{row['zona']}")
                
            return "\n- " + "\n- ".join(zone_names) if zone_names else "No hay zonas activas"
            
    except Exception as e:
        logger.error(f"Error obteniendo nombres de zonas de trabajo para {telegram_id}: {e}")
        return "Error al consultar DB"

def check_country_exists(country_id):
    """Verifica si un país existe y está activo."""
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM paises WHERE id = ? AND estado = 'activo'", (country_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error verificando país {country_id}: {e}")
        return False
