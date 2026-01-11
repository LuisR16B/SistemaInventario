import flet as ft
from data.database import obtener_usuario 

def login_view(page: ft.Page, on_login_success):
    
    async def btn_entrar_click(e):
        # Validación básica de campos vacíos
        if not txt_user.value or not txt_pass.value:
            mostrar_mensaje("Por favor, llena todos los campos")
            return

        user = obtener_usuario(txt_user.value, txt_pass.value)
        
        if user:
            page.user_id = user["id"]
            page.user_name = user.get("nombre", txt_user.value)
            await on_login_success()
        else:
            # Si las credenciales fallan, ahora sí verás el mensaje
            mostrar_mensaje("Usuario o contraseña incorrectos")

    def mostrar_mensaje(texto):
        """Función auxiliar para mostrar el SnackBar correctamente."""
        snack = ft.SnackBar(ft.Text(texto))
        # En versiones modernas, page.snack_bar es un shortcut, 
        # pero abrirlo manualmente es más seguro:
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- UI Limpia ---
    txt_user = ft.TextField(label="Usuario", width=300)
    txt_pass = ft.TextField(
        label="Contraseña", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        on_submit=btn_entrar_click # Permite dar 'Enter' para entrar
    )
    
    btn_principal = ft.ElevatedButton("ENTRAR", on_click=btn_entrar_click, width=300)

    return ft.Card(
        content=ft.Container(
            padding=30,
            content=ft.Column(
                horizontal_alignment="center",
                controls=[
                    ft.Text("INICIO DE SESIÓN", size=25, weight="bold"),
                    ft.Divider(height=20),
                    txt_user,
                    txt_pass,
                    ft.Container(height=10), # Espaciador
                    btn_principal,
                ],
                tight=True
            )
        )
    )