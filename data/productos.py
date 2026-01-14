from data.database import obtener_conexion

def buscar_productos(usuario_id, texto):
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM productos WHERE usuario_id = ? AND (nombre_producto LIKE ? OR codigo_barra LIKE ?) LIMIT 20"
        cursor.execute(query, (usuario_id, f"%{texto}%", f"%{texto}%"))
        return cursor.fetchall()
    finally:
        conn.close()

def insertar_producto(datos):
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        query = '''INSERT INTO productos 
                    (usuario_id, codigo_barra, nombre_producto, unidades_por_caja, 
                    precio_costo, porcentaje_transporte, precio_costo_total, 
                    porcentaje_venta, precio_venta, cantidad_unidades, marca_producto, categoria) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        cursor.execute(query, datos)
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def actualizar_producto(id_producto, datos_tupla):
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        query = '''UPDATE productos SET 
                    codigo_barra=?, nombre_producto=?, unidades_por_caja=?, 
                    precio_costo=?, porcentaje_transporte=?, precio_costo_total=?, 
                    porcentaje_venta=?, precio_venta=?, cantidad_unidades = cantidad_unidades + ?, 
                    marca_producto=?, categoria=? 
                    WHERE id = ?'''
        cursor.execute(query, datos_tupla + (id_producto,))
        conn.commit()
        return True
    finally:
        conn.close()

def obtener_inventario_paginado(usuario_id, busqueda, categoria, limite, offset):
    """Obtiene productos filtrados y paginados para la tabla de inventario."""
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        filtros = ["usuario_id = ?"]
        params = [usuario_id]

        if busqueda:
            filtros.append("(nombre_producto LIKE ? OR codigo_barra LIKE ? OR marca_producto LIKE ?)")
            term = f"{busqueda}%"
            params.extend([term, term, term])

        if categoria and categoria != "Todos":
            filtros.append("categoria = ?")
            params.append(categoria)

        where_sql = " WHERE " + " AND ".join(filtros)
        
        # Contar total
        cursor.execute(f"SELECT COUNT(*) FROM productos {where_sql}", params)
        total = cursor.fetchone()[0]

        # Obtener datos
        cursor.execute(f"SELECT * FROM productos {where_sql} LIMIT ? OFFSET ?", params + [limite, offset])
        productos = cursor.fetchall()
        
        return productos, total
    finally:
        conn.close()

def ajustar_stock_producto(producto_id, cantidad):
    """Suma o resta stock a un producto específico."""
    conn = obtener_conexion()
    try:
        conn.execute("UPDATE productos SET cantidad_unidades = cantidad_unidades + ? WHERE id = ?", 
                     (cantidad, producto_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()