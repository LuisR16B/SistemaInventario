import flet as ft
import os
from data.usuarios import obtener_usuario

def login_view(page: ft.Page, on_login_success):
    
    # --- LÓGICA PARA RUTA ABSOLUTA DEL LOGO ---
    directorio_actual = os.path.dirname(__file__)
    ruta_logo = os.path.join(directorio_actual, "..", "assets", "img", "logo.png")
    ruta_logo_absoluta = os.path.abspath(ruta_logo)

    page.bgcolor = "#00897b"
    
    async def btn_entrar_click(e):
        if not txt_user.value or not txt_pass.value:
            mostrar_mensaje("Por favor, llena todos los campos")
            return

        user = obtener_usuario(txt_user.value, txt_pass.value)
        
        if user:
            page.user_id = user["id"]
            page.user_name = user.get("nombre", txt_user.value)
            page.bgcolor = "white"
            await on_login_success()
        else:
            mostrar_mensaje("Usuario o contraseña incorrectos")

    def mostrar_mensaje(texto):
        snack = ft.SnackBar(ft.Text(texto))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- UI ---
    txt_user = ft.TextField(label="Usuario", width=350, color="black", border_color="#00897b")
    txt_pass = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=350, color="black", border_color="#00897b", on_submit=btn_entrar_click)
    btn_principal = ft.ElevatedButton("ENTRAR", on_click=btn_entrar_click, width=350, height=50, bgcolor="#00897b", color="white")

    return ft.Container(
        content=ft.Card(
            bgcolor="white",
            elevation=15,
            content=ft.Container(
                padding=ft.padding.only(top=20, bottom=20, left=40, right=40), # Padding reducido arriba y abajo
                width=500,       
                height=580,      # Altura reducida para quitar el exceso de blanco
                content=ft.Column(
                    horizontal_alignment="center",
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Image(
                            src=ruta_logo_absoluta, 
                            width=140, # Logo ligeramente más pequeño
                            height=140,
                            fit="contain",
                        ),
                        ft.Text("INICIO DE SESIÓN", size=26, weight="bold", color="black"),
                        ft.Divider(height=20, color="black12"), # Divisor más corto
                        txt_user,
                        ft.Container(height=5), # Menos espacio entre campos
                        txt_pass,
                        ft.Container(height=20), # Menos espacio antes del botón
                        btn_principal,
                    ],
                    tight=True # Ajusta la columna al contenido
                )
            )
        ),
        expand=True,
        alignment=ft.Alignment(0, 0) 
    )