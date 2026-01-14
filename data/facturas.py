import sqlite3
from datetime import datetime, timedelta
from .database import obtener_conexion

def guardar_factura_completa(usuario_id, datos_cliente, productos_carrito, monto_total):
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        
        # Gestionar Cliente
        cursor.execute("SELECT id FROM clientes WHERE usuario_id = ? AND cedula_rif = ?", 
                        (usuario_id, datos_cliente['cedula_rif']))
        cliente = cursor.fetchone()
        
        if cliente:
            cliente_id = cliente["id"]
            cursor.execute("UPDATE clientes SET email = ? WHERE id = ?", (datos_cliente.get('email'), cliente_id))
        else:
            cursor.execute('''INSERT INTO clientes (usuario_id, nombre_razon, cedula_rif, direccion, zona, email) 
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                           (usuario_id, datos_cliente['nombre_razon'], datos_cliente['cedula_rif'], 
                            datos_cliente['direccion'], datos_cliente['zona'], datos_cliente.get('email')))
            cliente_id = cursor.lastrowid

        # Fechas
        fecha_actual = datetime.now()
        fecha_vence = fecha_actual + timedelta(days=8)
        str_emision = fecha_actual.strftime("%Y-%m-%d")
        str_vence = fecha_vence.strftime("%Y-%m-%d")

        # Crear Factura
        cursor.execute('''INSERT INTO facturas (usuario_id, cliente_id, numero_factura, fecha_emision, fecha_vencimiento, monto_total, estado) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (usuario_id, cliente_id, "TEMP", str_emision, str_vence, monto_total, 'En Proceso'))
        
        factura_id = cursor.lastrowid
        num_fact_formateado = f"{factura_id:08d}"
        cursor.execute("UPDATE facturas SET numero_factura = ? WHERE id = ?", (num_fact_formateado, factura_id))

        # Detalles y Stock
        for p in productos_carrito:
            cursor.execute('''INSERT INTO factura_detalles (factura_id, producto_id, cantidad, precio_unitario, tipo) 
                              VALUES (?, ?, ?, ?, ?)''', 
                           (factura_id, p['id'], p['cantidad'], p['precio_unitario'], p['tipo']))
            
            cursor.execute("UPDATE productos SET cantidad_unidades = cantidad_unidades - ? WHERE id = ?", 
                            (p['unidades_totales'], p['id']))

        conn.commit()
        return {"success": True, "numero_factura": num_fact_formateado, "fecha_emision": str_emision, "fecha_vencimiento": str_vence}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def actualizar_facturas_vencidas():
    """Busca facturas 'En Proceso' cuya fecha ya pasó y las marca como 'Vencido'."""
    conn = obtener_conexion()
    try:
        hoy = datetime.now().strftime("%Y-%m-%d")
        conn.execute("UPDATE facturas SET estado = 'Vencido' WHERE estado = 'En Proceso' AND fecha_vencimiento < ?", (hoy,))
        conn.commit()
    finally:
        conn.close()

def obtener_historial_paginado(usuario_id, estado, texto_busqueda, limite, offset):
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        busqueda = f"%{texto_busqueda}%"
        
        cursor.execute("""
            SELECT COUNT(*) FROM facturas f JOIN clientes c ON f.cliente_id = c.id
            WHERE f.usuario_id = ? AND f.estado = ?
            AND (c.nombre_razon LIKE ? OR f.numero_factura LIKE ? OR c.cedula_rif LIKE ?)
        """, (usuario_id, estado, busqueda, busqueda, busqueda))
        total_items = cursor.fetchone()[0]

        cursor.execute("""
            SELECT f.*, c.nombre_razon, c.cedula_rif 
            FROM facturas f JOIN clientes c ON f.cliente_id = c.id
            WHERE f.usuario_id = ? AND f.estado = ?
            AND (c.nombre_razon LIKE ? OR f.numero_factura LIKE ? OR c.cedula_rif LIKE ?)
            ORDER BY f.id DESC LIMIT ? OFFSET ?
        """, (usuario_id, estado, busqueda, busqueda, busqueda, limite, offset))
        return cursor.fetchall(), total_items
    finally:
        conn.close()

def cambiar_estado_a_pagado(factura_id):
    conn = obtener_conexion()
    try:
        conn.execute("UPDATE facturas SET estado = 'Pagado' WHERE id = ?", (factura_id,))
        conn.commit()
    finally:
        conn.close()

def obtener_datos_detalle_factura(factura_id):
    """Obtiene los datos del cliente y los productos vendidos en una nota específica."""
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        # Obtener Cliente
        cursor.execute("""
            SELECT c.* FROM clientes c 
            JOIN facturas f ON f.cliente_id = c.id 
            WHERE f.id = ?
        """, (factura_id,))
        cliente = cursor.fetchone()

        # Obtener Productos del Detalle
        cursor.execute("""
            SELECT fd.*, p.nombre_producto 
            FROM factura_detalles fd
            JOIN productos p ON fd.producto_id = p.id
            WHERE fd.factura_id = ?
        """, (factura_id,))
        detalles = cursor.fetchall()

        return cliente, detalles
    finally:
        conn.close()