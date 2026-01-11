import flet as ft
from views.login_view import login_view

async def main(page: ft.Page):
    page.window.maximized = True
    page.title = "Prueba de Componente Login"
    page.theme_mode = "dark"
    
    # Configuramos alineación para que el Card aparezca en el centro
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    print(">>> Intentando renderizar login_view...")
    
    # Cargamos el componente directamente sin sistema de rutas
    login_component = login_view(page)
    
    # Lo añadimos a la página
    page.add(login_component)
    
    print(">>> Componente añadido. Si la ventana sigue negra, presiona Ctrl+R")
    page.update()

if __name__ == "__main__":
    # Probamos con el navegador para asegurar que el componente es válido
    # Si funciona aquí, cámbialo a ft.AppView.FLET_APP para probar en escritorio
    ft.run(main, view=ft.AppView.FLET_APP)