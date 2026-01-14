from data.database import obtener_conexion

def buscar_cliente_por_rif(usuario_id, texto):
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM clientes WHERE usuario_id = ? AND (cedula_rif LIKE ? OR nombre_razon LIKE ?)"
        cursor.execute(query, (usuario_id, f"%{texto}%", f"%{texto}%"))
        return cursor.fetchall()
    finally:
        conn.close()