import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join("database", "sistema_ventas.db")

def inicializar_db():
    """Crea la estructura completa de la base de datos."""
    if not os.path.exists("database"):
        os.makedirs("database")

    conn = sqlite3.connect(DB_PATH)
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
    
    # --- OPTIMIZACIÓN ---
    # Índice para acelerar la carga del historial y la paginación
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_paginacion ON facturas (usuario_id, estado, id DESC)')
    
    conn.commit()
    conn.close()

# --- GESTIÓN DE USUARIOS ---

def crear_usuario(nombre, password):
    """Crea un nuevo usuario con la contraseña encriptada."""
    conn = sqlite3.connect(DB_PATH)
    try:
        pass_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario_nombre, contrasenha) VALUES (?, ?)", (nombre, pass_hash))
        conn.commit()
        print(f"\n✅ Usuario '{nombre}' creado exitosamente.")
        return True
    except sqlite3.IntegrityError:
        print(f"\n❌ Error: El usuario '{nombre}' ya existe.")
        return False
    finally:
        conn.close()

def obtener_usuario(nombre, password_intento):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, usuario_nombre, contrasenha FROM usuarios WHERE usuario_nombre = ?", (nombre,))
        usuario = cursor.fetchone()
        if usuario and check_password_hash(usuario[2], password_intento):
            return {"id": usuario[0], "nombre": usuario[1]}
        return None
    except Exception as e:
        print(f"Error en Login: {e}")
        return None
    finally:
        conn.close()

# --- GESTIÓN DE PRODUCTOS ---

def buscar_productos(usuario_id, texto):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM productos WHERE usuario_id = ? AND (nombre_producto LIKE ? OR codigo_barra LIKE ?) LIMIT 20"
        cursor.execute(query, (usuario_id, f"%{texto}%", f"%{texto}%"))
        return cursor.fetchall()
    finally:
        conn.close()

def insertar_producto(datos):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = '''INSERT INTO productos 
                    (usuario_id, codigo_barra, nombre_producto, unidades_por_caja, 
                     precio_costo, porcentaje_transporte, precio_costo_total, 
                     porcentaje_venta, precio_venta, cantidad_unidades, marca_producto, categoria) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        cursor.execute(query, datos)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al insertar producto: {e}")
        return False
    finally:
        conn.close()

def actualizar_producto(id_producto, datos_tupla):
    try:
        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"Error al actualizar producto: {e}")
        return False
    finally:
        conn.close()

# --- GESTIÓN DE CLIENTES Y FACTURACIÓN ---

def buscar_cliente_por_rif(usuario_id, texto):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM clientes WHERE usuario_id = ? AND (cedula_rif LIKE ? OR nombre_razon LIKE ?)"
        cursor.execute(query, (usuario_id, f"%{texto}%", f"%{texto}%"))
        return cursor.fetchall()
    finally:
        conn.close()

def guardar_factura_completa(usuario_id, datos_cliente, productos_carrito, monto_total):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Buscar o Crear Cliente
        cursor.execute("SELECT id FROM clientes WHERE usuario_id = ? AND cedula_rif = ?", 
                        (usuario_id, datos_cliente['cedula_rif']))
        cliente = cursor.fetchone()
        
        if cliente:
            cliente_id = cliente[0]
            cursor.execute("UPDATE clientes SET email = ? WHERE id = ?", (datos_cliente.get('email'), cliente_id))
        else:
            cursor.execute('''INSERT INTO clientes (usuario_id, nombre_razon, cedula_rif, direccion, zona, email) 
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                           (usuario_id, datos_cliente['nombre_razon'], datos_cliente['cedula_rif'], 
                            datos_cliente['direccion'], datos_cliente['zona'], datos_cliente.get('email')))
            cliente_id = cursor.lastrowid

        # 2. Generación de Fechas y Número de Factura
        fecha_actual = datetime.now()
        fecha_vence = fecha_actual + timedelta(days=8)
        str_emision = fecha_actual.strftime("%d-%m-%Y")
        str_vence = fecha_vence.strftime("%d-%m-%Y")

        cursor.execute('''INSERT INTO facturas (usuario_id, cliente_id, numero_factura, fecha_emision, fecha_vencimiento, monto_total, estado) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                       (usuario_id, cliente_id, "TEMP", str_emision, str_vence, monto_total, 'En Proceso'))
        
        factura_id = cursor.lastrowid
        num_fact_formateado = f"{factura_id:08d}"
        
        cursor.execute("UPDATE facturas SET numero_factura = ? WHERE id = ?", (num_fact_formateado, factura_id))

        # 3. Detalles y Actualización de Stock
        for p in productos_carrito:
            cursor.execute('''INSERT INTO factura_detalles (factura_id, producto_id, cantidad, precio_unitario, tipo) 
                              VALUES (?, ?, ?, ?, ?)''', 
                           (factura_id, p['id'], p['cantidad'], p['precio_unitario'], p['tipo']))
            
            cursor.execute("UPDATE productos SET cantidad_unidades = cantidad_unidades - ? WHERE id = ?", 
                            (p['unidades_totales'], p['id']))

        conn.commit()
        return {
            "success": True, 
            "numero_factura": num_fact_formateado, 
            "fecha_emision": str_emision, 
            "fecha_vencimiento": str_vence
        }
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error DB: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if conn: conn.close()

# --- INTERFAZ DE CONSOLA ---

if __name__ == "__main__":
    inicializar_db()
    while True:
        print("\n=== PANEL DE CONTROL DE BASE DE DATOS ===")
        print("1. Agregar nuevo usuario")
        print("2. Listar usuarios existentes")
        print("3. Salir")
        
        opcion = input("\nSeleccione una opción: ").strip()
        
        if opcion == '1':
            u = input("Nombre de usuario deseado: ").strip()
            p = input("Contraseña para el usuario: ").strip()
            if u and p:
                crear_usuario(u, p)
            else:
                print("⚠️ Error: Los campos no pueden estar vacíos.")
        
        elif opcion == '2':
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, usuario_nombre FROM usuarios")
            usuarios = cursor.fetchall()
            print("\n--- Usuarios en el Sistema ---")
            for user in usuarios:
                print(f"ID: {user[0]} | Nombre: {user[1]}")
            conn.close()
        
        elif opcion == '3':
            print("Cerrando panel...")
            break
        
        else:
            print("Opción no válida.")