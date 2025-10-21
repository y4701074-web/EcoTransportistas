import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "ecotransportistas.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Inicializar todas las tablas de la base de datos"""
        tables = [
            # Tabla de usuarios
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                nombre_completo TEXT NOT NULL,
                telefono TEXT NOT NULL,
                tipo TEXT NOT NULL,
                pais TEXT DEFAULT 'Cuba',
                provincia TEXT,
                zona TEXT,
                estado TEXT DEFAULT 'activo',
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Tabla de administradores (simplificada por ahora)
            """
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER UNIQUE NOT NULL,
                nivel TEXT NOT NULL,
                region_asignada TEXT NOT NULL,
                estado TEXT DEFAULT 'activo',
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(table)
            
            # Insertar admin supremo si no existe
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (8405097042,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO usuarios (telegram_id, username, nombre_completo, telefono, tipo, pais, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (8405097042, "Y_0304", "Jorge Yasir Rivas Del Río", "+5351234567", "admin_supremo", "Cuba", "activo")
                )
                
            conn.commit()
            logger.info("✅ Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
        finally:
            conn.close()
    
    # ========== MÉTODOS PARA USUARIOS ==========
    
    def obtener_usuario_por_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Obtener usuario por su ID de Telegram"""
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM usuarios WHERE telegram_id = ?", (telegram_id,))
            usuario = cursor.fetchone()
            
            return dict(usuario) if usuario else None
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None
        finally:
            conn.close()
    
    def registrar_usuario(self, telegram_id: int, username: str, nombre_completo: str, 
                         telefono: str, tipo: str, pais: str = "Cuba", 
                         provincia: str = None, zona: str = None) -> bool:
        """Registrar un nuevo usuario en el sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO usuarios 
                (telegram_id, username, nombre_completo, telefono, tipo, pais, provincia, zona) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (telegram_id, username, nombre_completo, telefono, tipo, pais, provincia, zona)
            )
            
            conn.commit()
            logger.info(f"✅ Usuario {nombre_completo} registrado exitosamente")
            return True
        except sqlite3.IntegrityError:
            logger.warning("⚠️ Usuario ya existe en la base de datos")
            return False
        except Exception as e:
            logger.error(f"❌ Error registrando usuario: {e}")
            return False
        finally:
            conn.close()
    
    def obtener_estadisticas_sistema(self) -> Dict:
        """Obtener estadísticas básicas del sistema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total de usuarios
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = cursor.fetchone()[0]
            
            # Usuarios activos
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE estado = 'activo'")
            usuarios_activos = cursor.fetchone()[0]
            
            # Contar por tipo
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo LIKE '%transportista%'")
            total_transportistas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo LIKE '%solicitante%'")
            total_solicitantes = cursor.fetchone()[0]
            
            return {
                'total_usuarios': total_usuarios,
                'usuarios_activos': usuarios_activos,
                'total_transportistas': total_transportistas,
                'total_solicitantes': total_solicitantes,
                'estado_bd': '🟢 OPERATIVA'
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                'total_usuarios': 0,
                'usuarios_activos': 0,
                'total_transportistas': 0,
                'total_solicitantes': 0,
                'estado_bd': '🔴 ERROR'
            }
        finally:
            conn.close()
    
    def obtener_estadisticas_detalladas(self) -> Dict:
        """Obtener estadísticas detalladas del sistema"""
        stats = self.obtener_estadisticas_sistema()
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Usuarios con ambos roles
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'ambos'")
            usuarios_ambos = cursor.fetchone()[0]
            
            # Transportistas activos
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo LIKE '%transportista%' AND estado = 'activo'")
            transportistas_activos = cursor.fetchone()[0]
            
            # Solicitantes activos
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo LIKE '%solicitante%' AND estado = 'activo'")
            solicitantes_activos = cursor.fetchone()[0]
            
            stats.update({
                'usuarios_ambos': usuarios_ambos,
                'transportistas_activos': transportistas_activos,
                'solicitantes_activos': solicitantes_activos
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas detalladas: {e}")
        
        return stats
