import flet as ft
import asyncio
from data.database import inicializar_db
from views.login_view import login_view
# Importamos la nueva vista que creamos
from views.agregar_producto_view import agregar_producto_view

async def main(page: ft.Page):
    page.window.maximized = True
    page.title = "StockSmart Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    # Inicializar la base de datos al arrancar
    inicializar_db()

    # Variable para rastrear la sección activa
    page.selected_menu = "Inventario"

    # Contenedor dinámico principal (Lado derecho)
    content_area = ft.Container(
        expand=True,
        padding=30,
        bgcolor="#F4F6F7",
        content=ft.Text("Iniciando...", color="black")
    )

    async def show_login():
        page.controls.clear()
        page.add(
            ft.Container(
                content=login_view(page, on_login_success=show_inventario),
                alignment=ft.Alignment(0, 0),
                expand=True
            )
        )
        page.update()

    async def cambiar_pestaña(nombre_seccion):
        page.selected_menu = nombre_seccion
        actualizar_sidebar()
        
        # Lógica de enrutamiento a las vistas
        if nombre_seccion == "Agregar Producto":
            content_area.content = agregar_producto_view(page)
        elif nombre_seccion == "Inventario":
            # Aquí irá la vista de inventario con paginación
            content_area.content = ft.Column([
                ft.Text(nombre_seccion, size=30, weight="bold", color="#004d40"),
                ft.Text("Módulo de inventario en desarrollo...", color="black54")
            ])
        else:
            content_area.content = ft.Column([
                ft.Text(nombre_seccion, size=30, weight="bold", color="#004d40"),
                ft.Divider(color="black12"),
                ft.Text(f"Sección de {nombre_seccion} lista para programar.", color="black54")
            ])
        
        page.update()

    def build_menu_button(texto):
        """Crea los botones de la barra lateral con el diseño de la captura."""
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

    # Columna que aloja los botones del menú
    rail = ft.Column(spacing=0)

    def actualizar_sidebar():
        secciones = ["Agregar Producto", "Inventario", "Crear Factura", "Historial", "Finanzas"]
        rail.controls = [build_menu_button(s) for s in secciones]

    async def show_inventario():
        u_name = getattr(page, "user_name", "Usuario")
        page.controls.clear()

        # Cargar botones iniciales
        actualizar_sidebar()

        app_bar = ft.AppBar(
            title=ft.Text(f"STOCKSMART - {u_name.upper()}", weight="bold", color="white"),
            bgcolor="#00332a",
            actions=[ft.TextButton("SALIR", on_click=lambda _: logout_task())]
        )

        # Contenedor de la barra lateral (Verde oscuro)
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

        # Mostrar "Agregar Producto" por defecto al entrar
        content_area.content = agregar_producto_view(page)
        page.selected_menu = "Agregar Producto"
        actualizar_sidebar()

        page.add(app_bar, layout)
        page.update()

    def logout_task():
        asyncio.create_task(show_login())

    # Iniciar con el Login
    await show_login()

if __name__ == "__main__":
    ft.run(main)