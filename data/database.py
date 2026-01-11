import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join("database", "sistema_ventas.db")

def inicializar_db():
    """Crea las tablas de Usuarios y Productos actualizadas."""
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

    # 2. TABLA PRODUCTOS (Sin IVA y conectada al Usuario)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            codigo_barra TEXT,
            nombre_producto TEXT NOT NULL,
            unidades TEXT,
            precio_costo REAL,
            porcentaje REAL,
            precio_venta REAL,
            cantidad INTEGER DEFAULT 0,
            marca_producto TEXT,
            categoria TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# --- GESTIÓN DE USUARIOS ---

def obtener_usuario(nombre, password_intento):
    """Verifica credenciales para el Login."""
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

# --- GESTIÓN DE PRODUCTOS CON PAGINACIÓN ---

def insertar_producto(datos):
    """Inserta un nuevo producto."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = '''INSERT INTO productos 
                   (usuario_id, codigo_barra, nombre_producto, unidades, precio_costo, 
                    porcentaje, precio_venta, cantidad, marca_producto, categoria) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        cursor.execute(query, datos)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al insertar producto: {e}")
        return False
    finally:
        conn.close()

def obtener_productos_paginados(usuario_id, pagina_actual, productos_por_pagina=10):
    """Retorna los productos de un usuario usando LIMIT y OFFSET."""
    offset = (pagina_actual - 1) * productos_por_pagina
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM productos WHERE usuario_id = ? LIMIT ? OFFSET ?",
            (usuario_id, productos_por_pagina, offset)
        )
        return cursor.fetchall()
    finally:
        conn.close()

def contar_total_productos(usuario_id):
    """Retorna el número total de productos para calcular el número de páginas."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos WHERE usuario_id = ?", (usuario_id,))
        total = cursor.fetchone()[0]
        return total
    finally:
        conn.close()

# --- SCRIPT PARA CONSOLA ---
# Ejecuta este archivo directamente: python data/database.py
if __name__ == "__main__":
    inicializar_db()
    print("\n--- REGISTRO DE USUARIOS POR CONSOLA ---")
    user = input("Nuevo usuario: ")
    pw = input("Contraseña: ")
    
    hash_pw = generate_password_hash(pw)
    try:
        db = sqlite3.connect(DB_PATH)
        db.execute("INSERT INTO usuarios (usuario_nombre, contrasenha) VALUES (?,?)", (user, hash_pw))
        db.commit()
        db.close()
        print(f"\nExito: Usuario '{user}' creado correctamente.")
    except Exception as e:
        print(f"\nError: El usuario ya existe o hubo un problema: {e}")