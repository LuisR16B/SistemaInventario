import flet as ft
import asyncio
from data.database import inicializar_db
from views.login_view import login_view
from views.agregar_producto_view import agregar_producto_view
from views.inventario_view import inventario_view

async def main(page: ft.Page):
    page.window.maximized = True
    page.title = "ZAMORA 77"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    # Inicializar la base de datos al arrancar
    inicializar_db()

    # Variable para rastrear la sección activa
    page.selected_menu = "Agregar Producto"

    # Contenedor dinámico principal
    content_area = ft.Container(
        expand=True,
        padding=30,
        bgcolor="#F4F6F7",
        content=ft.Text("Cargando módulo...", color="black")
    )

    async def show_login():
        page.controls.clear()
        page.add(
            ft.Container(
                content=login_view(page, on_login_success=show_panel_principal),
                alignment=ft.Alignment(0, 0),
                expand=True
            )
        )
        page.update()

    async def cambiar_pestaña(nombre_seccion):
        page.selected_menu = nombre_seccion
        actualizar_sidebar()
        
        if nombre_seccion == "Agregar Producto":
            content_area.content = agregar_producto_view(page)
        elif nombre_seccion == "Inventario":
            content_area.content = inventario_view(page)
        else:
            content_area.content = ft.Column([
                ft.Text(nombre_seccion, size=28, weight="bold", color="#00332a"),
                ft.Divider(color="#00332a"),
                ft.Text(f"El módulo de {nombre_seccion} está en desarrollo.", color="black", size=16)
            ])
        
        page.update()

    def build_menu_button(texto):
        is_selected = page.selected_menu == texto
        return ft.Container(
            content=ft.Text(texto, color="white", size=15, weight=ft.FontWeight.W_500),
            padding=ft.Padding(left=25, top=18, right=0, bottom=18),
            bgcolor="#00897b" if is_selected else None,
            on_click=lambda _: asyncio.create_task(cambiar_pestaña(texto)),
            alignment=ft.Alignment(-1, 0),
            width=250,
            border_radius=0,
            ink=True,
        )

    rail = ft.Column(spacing=0)

    def actualizar_sidebar():
        secciones = ["Agregar Producto", "Inventario", "Crear Factura", "Historial", "Finanzas"]
        rail.controls = [build_menu_button(s) for s in secciones]

    async def show_panel_principal():
        u_name = getattr(page, "user_name", "Usuario")
        page.controls.clear()

        actualizar_sidebar()

        # Corrección del error 'color' en TextButton usando ft.ButtonStyle
        app_bar = ft.AppBar(
            title=ft.Text(f"ZAMORA 77 - {u_name.upper()}", weight="bold", color="white"),
            bgcolor="#00332a",
            center_title=False,
            actions=[
                ft.Container(
                    content=ft.TextButton(
                        "CERRAR SESIÓN", 
                        on_click=lambda _: logout_task(),
                        style=ft.ButtonStyle(color="white") # Forma correcta en versiones nuevas
                    ),
                    padding=ft.Padding(right=20, top=0, left=0, bottom=0)
                )
            ]
        )

        rail_container = ft.Container(
            content=rail,
            width=220,
            bgcolor="#004d40",
            expand=False,
        )

        layout = ft.Row(
            controls=[
                rail_container,
                content_area,
            ],
            expand=True,
            spacing=0,
        )

        # Cargar la vista por defecto
        content_area.content = agregar_producto_view(page)
        
        page.add(app_bar, layout)
        page.update()

    def logout_task():
        asyncio.create_task(show_login())

    await show_login()

if __name__ == "__main__":
    ft.run(main)
