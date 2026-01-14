import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join("database", "sistema_ventas.db")

def obtener_conexion():
    """Establece conexión con la base de datos y usa Row Factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    """Crea la estructura de carpetas y todas las tablas necesarias."""
    if not os.path.exists("database"):
        os.makedirs("database")

    conn = obtener_conexion()
    cursor = conn.cursor()

    # 1. TABLA USUARIOS (Incluyendo ROL)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_nombre TEXT NOT NULL UNIQUE,
            contrasenha TEXT NOT NULL,
            rol TEXT DEFAULT 'empresa'
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

    # 6. TABLA MOVIMIENTOS DE CAJA (Para Finanzas/Socios)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL, 
            monto REAL NOT NULL,
            descripcion TEXT,
            fecha TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_paginacion ON facturas (usuario_id, estado, id DESC)')
    
    conn.commit()
    conn.close()

# --- NUEVA FUNCIÓN PARA LA CONSOLA ---

def menu_crear_usuario_consola():
    """Permite registrar un usuario con rol desde la terminal."""
    print("\n" + "="*40)
    print("   REGISTRO MANUAL DE USUARIOS")
    print("="*40)
    
    nombre = input("Nombre de usuario: ").strip()
    password = input("Contraseña: ").strip()
    
    if not nombre or not password:
        print("\n❌ Error: No se permiten campos vacíos.")
        return

    print("\nSeleccione el Rol:")
    print("1. Empresa (Administrativo)")
    print("2. Socio (Finanzas Compartidas 50/50)")
    opcion = input("Elija opción (1 o 2): ")
    
    rol = "socio" if opcion == "2" else "empresa"
    
    # Hashear la contraseña para que sea compatible con el login
    pass_hash = generate_password_hash(password)

    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (usuario_nombre, contrasenha, rol) VALUES (?, ?, ?)",
            (nombre, pass_hash, rol)
        )
        conn.commit()
        print(f"\n✅ Usuario '{nombre}' creado exitosamente como '{rol}'.")
    except sqlite3.IntegrityError:
        print(f"\n❌ Error: El usuario '{nombre}' ya existe.")
    finally:
        conn.close()

if __name__ == "__main__":
    inicializar_db()
    # Si ejecutas 'python data/database.py', se abrirá el menú de creación
    menu_crear_usuario_consola()