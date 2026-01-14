import sqlite3
import os

DB_PATH = os.path.join("database", "sistema_ventas.db")

def obtener_conexion():
    """Establece conexión con la base de datos y usa Row Factory para acceder por nombre de columna."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    """Crea la estructura de carpetas y todas las tablas necesarias."""
    if not os.path.exists("database"):
        os.makedirs("database")

    conn = obtener_conexion()
    cursor = conn.cursor()

    # 1. TABLA USUARIOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_nombre TEXT NOT NULL UNIQUE,
            contrasenha TEXT NOT NULL
        )
    ''')

    # 2. TABLA PRODUCTOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            codigo_barra TEXT,
            nombre_producto TEXT NOT NULL,
            unidades_por_caja INTEGER DEFAULT 1,
            precio_costo REAL DEFAULT 0,
            porcentaje_transporte REAL DEFAULT 0,
            precio_costo_total REAL DEFAULT 0,
            porcentaje_venta REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            cantidad_unidades INTEGER DEFAULT 0,
            marca_producto TEXT,
            categoria TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    # 3. TABLA CLIENTES
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nombre_razon TEXT NOT NULL,
            cedula_rif TEXT NOT NULL,
            direccion TEXT,
            zona TEXT,
            email TEXT,
            UNIQUE(usuario_id, cedula_rif),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # 4. TABLA FACTURAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            numero_factura TEXT NOT NULL,
            fecha_emision TEXT NOT NULL,
            fecha_vencimiento TEXT,
            monto_total REAL DEFAULT 0,
            estado TEXT DEFAULT 'En Proceso',
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # 5. DETALLES DE FACTURA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factura_detalles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            tipo TEXT NOT NULL,
            FOREIGN KEY (factura_id) REFERENCES facturas (id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_paginacion ON facturas (usuario_id, estado, id DESC)')
    
    conn.commit()
    conn.close()