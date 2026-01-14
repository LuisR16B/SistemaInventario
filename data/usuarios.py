from werkzeug.security import generate_password_hash, check_password_hash
from data.database import obtener_conexion

def crear_usuario(nombre, password, rol="empresa"):
    conn = obtener_conexion()
    try:
        pass_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (usuario_nombre, contrasenha, rol) VALUES (?, ?, ?)", 
            (nombre, pass_hash, rol)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        return False
    finally:
        conn.close()

def obtener_usuario(nombre, password_intento):
    conn = obtener_conexion()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, usuario_nombre, contrasenha, rol FROM usuarios WHERE usuario_nombre = ?", 
            (nombre,)
        )
        usuario = cursor.fetchone()
        
        if usuario and check_password_hash(usuario["contrasenha"], password_intento):
            return {
                "id": usuario["id"], 
                "nombre": usuario["usuario_nombre"],
                "rol": usuario["rol"]
            }
        return None
    finally:
        conn.close()