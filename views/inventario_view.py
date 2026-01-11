import flet as ft
from data.database import obtener_productos_paginados, contar_total_productos

def inventario_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    
    # --- VARIABLES DE ESTADO ---
    pagina_actual = 1
    productos_por_pagina = 10

    # --- COMPONENTES DE LA INTERFAZ ---
    txt_info_paginacion = ft.Text(color="black", weight="bold")
    
    tabla = ft.DataTable(
        bgcolor="white",
        border=ft.border.all(1, "black12"),
        border_radius=10,
        vertical_lines=ft.border.BorderSide(1, "black12"),
        heading_row_color="#004d40",
        columns=[
            ft.DataColumn(ft.Text("CÓDIGO", color="white", weight="bold")),
            ft.DataColumn(ft.Text("NOMBRE", color="white", weight="bold")),
            ft.DataColumn(ft.Text("MARCA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("COSTO", color="white", weight="bold")),
            ft.DataColumn(ft.Text("VENTA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("STOCK", color="white", weight="bold")),
        ],
        rows=[]
    )

    def cargar_datos():
        nonlocal pagina_actual
        # 1. Obtener productos de la DB
        productos = obtener_productos_paginados(user_id, pagina_actual, productos_por_pagina)
        # 2. Obtener total para la info de paginación
        total_prods = contar_total_productos(user_id)
        total_paginas = (total_prods + productos_por_pagina - 1) // productos_por_pagina

        # 3. Limpiar y llenar filas
        tabla.rows.clear()
        for p in productos:
            # Alerta visual si hay poco stock
            stock_color = "red" if p['cantidad'] <= 5 else "black"
            
            tabla.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p['codigo_barra'], color="black")),
                    ft.DataCell(ft.Text(p['nombre_producto'], color="black")),
                    ft.DataCell(ft.Text(p['marca_producto'], color="black")),
                    ft.DataCell(ft.Text(f"$ {p['precio_costo']}", color="black")),
                    ft.DataCell(ft.Text(f"$ {p['precio_venta']}", color="black")),
                    ft.DataCell(ft.Text(str(p['cantidad']), color=stock_color, weight="bold")),
                ])
            )
        
        # 4. Actualizar info inferior
        txt_info_paginacion.value = f"Página {pagina_actual} de {max(1, total_paginas)} (Total: {total_prods} productos)"
        
        # 5. Habilitar/Deshabilitar botones
        btn_prev.disabled = (pagina_actual == 1)
        btn_next.disabled = (pagina_actual >= total_paginas)
        page.update()

    # --- FUNCIONES DE NAVEGACIÓN ---
    def proxima_pagina(e):
        nonlocal pagina_actual
        pagina_actual += 1
        cargar_datos()

    def anterior_pagina(e):
        nonlocal pagina_actual
        pagina_actual -= 1
        cargar_datos()

    # --- BOTONES DE PAGINACIÓN ---
    btn_prev = ft.ElevatedButton(
        "ANTERIOR", 
        on_click=anterior_pagina, 
        bgcolor="#004d40", 
        color="white"
    )
    btn_next = ft.ElevatedButton(
        "SIGUIENTE", 
        on_click=proxima_pagina, 
        bgcolor="#004d40", 
        color="white"
    )

    # Cargar datos por primera vez
    cargar_datos()

    return ft.Column([
        ft.Row([
            ft.Text("INVENTARIO GENERAL", size=28, weight="bold", color="#00332a"),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "ACTUALIZAR TABLA", 
                on_click=lambda _: cargar_datos(),
                bgcolor="#00897b",
                color="white"
            )
        ]),
        ft.Divider(color="#00332a", height=2),
        
        # Contenedor con scroll horizontal por si la tabla es muy ancha
        ft.Row([tabla], scroll=ft.ScrollMode.AUTO),
        
        # Barra de navegación inferior
        ft.Row([
            btn_prev,
            ft.Container(content=txt_info_paginacion, padding=10),
            btn_next
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        
    ], spacing=20, scroll=ft.ScrollMode.AUTO)