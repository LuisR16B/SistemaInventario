import flet as ft
import sqlite3
from data.database import DB_PATH

def inventario_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)

    # --- VARIABLES DE ESTADO ---
    state = {"pagina": 1, "por_pagina": 8}

    # --- ESTILO ---
    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="black", weight="bold"),
        "border_color": "#004d40",
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
    }

    # --- FUNCIÓN DE CARGA Y FILTRADO ---
    def ejecutar_filtro(e=None):
        state["pagina"] = 1
        cargar_datos()

    def cargar_datos():
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            filtros = ["usuario_id = ?"]
            params = [user_id]

            busqueda = txt_busqueda.value.strip() if txt_busqueda.value else ""
            categoria = drop_categoria.value

            if busqueda:
                # Filtro por prefijo (inicio de palabra)
                filtros.append("(nombre_producto LIKE ? OR codigo_barra LIKE ? OR marca_producto LIKE ?)")
                term = f"{busqueda}%"
                params.extend([term, term, term])

            if categoria and categoria != "Todos":
                filtros.append("categoria = ?")
                params.append(categoria)

            where_sql = " WHERE " + " AND ".join(filtros)

            cursor.execute(f"SELECT COUNT(*) FROM productos {where_sql}", params)
            total_prods = cursor.fetchone()[0]
            total_paginas = (total_prods + state["por_pagina"] - 1) // state["por_pagina"]

            offset = (state["pagina"] - 1) * state["por_pagina"]
            query_final = f"SELECT * FROM productos {where_sql} LIMIT ? OFFSET ?"
            cursor.execute(query_final, params + [state["por_pagina"], offset])
            
            productos = cursor.fetchall()
            conn.close()

            tabla.rows.clear()
            for p in productos:
                stock = p['cantidad_unidades']
                tabla.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(p['codigo_barra'] or "N/A", color="black")),
                        ft.DataCell(ft.Text(p['nombre_producto'], color="black")),
                        ft.DataCell(ft.Text(p['categoria'] or "S/C", color="black")),
                        ft.DataCell(ft.Text(p['marca_producto'] or "S/M", color="black")),
                        ft.DataCell(ft.Text(f"$ {p['precio_costo_total']:.2f}", color="black")),
                        ft.DataCell(ft.Text(f"$ {p['precio_venta']:.2f}", color="black")),
                        ft.DataCell(ft.Text(str(stock), color="red" if stock <= 5 else "black", weight="bold")),
                    ])
                )

            txt_info_paginacion.value = f"Página {state['pagina']} de {max(1, total_paginas)} (Total: {total_prods})"
            btn_prev.disabled = state["pagina"] == 1
            btn_next.disabled = state["pagina"] >= total_paginas
            
            page.update()

        except Exception as ex:
            print(f"Error: {ex}")

    # --- COMPONENTES ---

    txt_busqueda = ft.TextField(
        label="Buscar...",
        expand=True,
        on_change=ejecutar_filtro,
        **estilo_campo
    )

    # CORRECCIÓN AQUÍ: Definimos el Dropdown y luego asignamos el evento
    drop_categoria = ft.Dropdown(
        label="Categoría",
        width=200,
        options=[
            ft.dropdown.Option("Todos"),
            ft.dropdown.Option("Alimentos"),
            ft.dropdown.Option("Bebidas"),
            ft.dropdown.Option("Limpieza"),
            ft.dropdown.Option("papeleria"),
        ],
        value="Todos",
        **estilo_campo
    )
    # Asignación manual para evitar el TypeError
    drop_categoria.on_change = ejecutar_filtro

    btn_filtrar = ft.ElevatedButton(
        "FILTRAR",
        bgcolor="#004d40",
        color="white",
        height=50,
        on_click=ejecutar_filtro
    )

    tabla = ft.DataTable(
        bgcolor="white",
        border=ft.border.all(1, "black12"),
        border_radius=10,
        heading_row_color="#004d40",
        column_spacing=40,
        columns=[
            ft.DataColumn(ft.Text("CÓDIGO", color="white", weight="bold")),
            ft.DataColumn(ft.Text("NOMBRE", color="white", weight="bold")),
            ft.DataColumn(ft.Text("CATEGORÍA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("MARCA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("COSTO TOTAL", color="white", weight="bold")),
            ft.DataColumn(ft.Text("PRECIO VENTA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("STOCK", color="white", weight="bold")),
        ],
    )

    # --- NAVEGACIÓN ---
    def nav_ant(e):
        if state["pagina"] > 1:
            state["pagina"] -= 1
            cargar_datos()

    def nav_sig(e):
        state["pagina"] += 1
        cargar_datos()

    btn_prev = ft.ElevatedButton("ANTERIOR", on_click=nav_ant, bgcolor="#004d40", color="white")
    btn_next = ft.ElevatedButton("SIGUIENTE", on_click=nav_sig, bgcolor="#004d40", color="white")
    txt_info_paginacion = ft.Text(color="black", weight="bold")

    cargar_datos()

    return ft.Column([
        ft.Text("INVENTARIO GENERAL", size=28, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=1, thickness=1),
        
        ft.Row(controls=[txt_busqueda, drop_categoria, btn_filtrar], spacing=10),
        
        ft.ListView(
            [tabla],
            expand=True,
            spacing=0,
            padding=0, 
        ),
        
        ft.Row(
            [btn_prev, ft.Container(txt_info_paginacion, padding=10), btn_next],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )
    ], spacing=20, expand=True)