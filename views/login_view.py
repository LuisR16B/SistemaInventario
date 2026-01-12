import flet as ft
from data.database import obtener_usuario 

def login_view(page: ft.Page, on_login_success):
    
    # Fondo de la pantalla (Verde)
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
    # Aumentamos un poco el ancho de los campos para que luzcan mejor en el cuadro grande
    txt_user = ft.TextField(
        label="Usuario", 
        width=350,
        color="black",
        border_color="#00897b"
    )
    
    txt_pass = ft.TextField(
        label="Contraseña", 
        password=True, 
        can_reveal_password=True, 
        width=350,
        color="black",
        border_color="#00897b",
        on_submit=btn_entrar_click 
    )
    
    btn_principal = ft.ElevatedButton(
        "ENTRAR", 
        on_click=btn_entrar_click, 
        width=350,
        height=50, # Botón un poco más alto
        bgcolor="#00897b",
        color="white"
    )

    return ft.Container(
        content=ft.Card(
            bgcolor="white",
            elevation=15, # Un poco más de sombra para resaltar el tamaño
            content=ft.Container(
                padding=60,      # Más espacio interno
                width=500,       # Ancho aumentado (antes 380)
                height=600,      # Alto aumentado para que sea un cuadrado grande
                content=ft.Column(
                    horizontal_alignment="center",
                    alignment=ft.MainAxisAlignment.CENTER, # Centra el contenido verticalmente
                    controls=[
                        ft.Text("INICIO DE SESIÓN", size=30, weight="bold", color="black"),
                        ft.Divider(height=40, color="black12"),
                        txt_user,
                        ft.Container(height=10), # Espacio entre campos
                        txt_pass,
                        ft.Container(height=30), # Espacio antes del botón
                        btn_principal,
                    ],
                    tight=True
                )
            )
        ),
        expand=True,
        alignment=ft.Alignment(0, 0) 
    )