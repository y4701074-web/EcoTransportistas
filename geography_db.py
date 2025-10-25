def get_geographic_level_name(level, id_):
    """Obtiene el nombre de un país, provincia o zona dado su ID y nivel."""
    if not id_:
        return "N/A"
        
    try:
        with sqlite3.connect(DATABASE_FILE, timeout=10) as conn:
            cursor = conn.cursor()
            
            # ✅ CORREGIR: Mapear niveles a nombres de tabla correctos
            table_map = {
                'pais': 'paises',
                'provincia': 'provincias', 
                'zona': 'zonas'
            }
            
            table = table_map.get(level)
            if not table:
                return "Nivel desconocido"
            
            cursor.execute(f"SELECT nombre FROM {table} WHERE id = ?", (id_,))
            result = cursor.fetchone()
            return result[0] if result else "Desconocido"
            
    except Exception as e:
        logger.error(f"Error obteniendo nombre geográfico para {level} ID {id_}: {e}")
        return "ERROR_DB"