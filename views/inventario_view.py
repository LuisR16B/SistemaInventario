import flet as ft
from data.productos import obtener_inventario_paginado, ajustar_stock_producto

def inventario_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    state = {"pagina": 1, "por_pagina": 8}

    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="#004d40", weight="bold"),
        "border_color": "#004d40",
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
        "bgcolor": "white",
    }

    def mostrar_mensaje(texto, color="#c62828", color_text="white"):
        snack = ft.SnackBar(ft.Text(texto, color=color_text),  bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- VENTANA EMERGENTE CORREGIDA ---
    def abrir_ajuste_stock(producto_id, nombre_prod, stock_actual):
        # TRUNCAR NOMBRE PARA EL TÍTULO: Si es muy largo, corta y pone "..."
        nombre_mostrado = (nombre_prod[:15] + "...") if len(nombre_prod) > 15 else nombre_prod

        txt_cantidad_ajuste = ft.TextField(
            label="Cantidad a sumar o restar",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_align=ft.TextAlign.CENTER,
            expand=True,
            **estilo_campo
        )

        def guardar_ajuste_db(e):
            try:
                cantidad = int(txt_cantidad_ajuste.value)
                if cantidad < 0 and (stock_actual + cantidad) < 0:
                    mostrar_mensaje(f"Error: Stock insuficiente. Solo hay {stock_actual} disponibles.")
                    return
                
                if ajustar_stock_producto(producto_id, cantidad):
                    dlg_ajuste.open = False
                    mostrar_mensaje(f"Stock actualizado correctamente", color="#004d40")
                    cargar_datos() 
                    page.update()
                else:
                    mostrar_mensaje("Error al actualizar en la base de datos")
            except ValueError:
                mostrar_mensaje("Error: Ingresa un número entero válido")

        dlg_ajuste = ft.AlertDialog(
            bgcolor="white",
            shape=ft.RoundedRectangleBorder(radius=10),
            # TÍTULO CON NOMBRE TRUNCADO
            title=ft.Text(f"Ajustar Stock: {nombre_mostrado}", color="#004d40", weight="bold"),
            content=ft.Container(
                width=400, # ESTO define el ancho de la ventana emergente
                content=ft.Column([
                    ft.Container(
                        padding=10, 
                        bgcolor="#E0F2F1", 
                        border_radius=5,
                        alignment=ft.Alignment.CENTER,
                        # Hacemos que la caja de stock también cubra el ancho
                        width=float("inf"), 
                        content=ft.Text(f"Stock actual: {stock_actual}", color="#00695C", weight="bold")
                    ),
                    # Al estar dentro de una Column, el TextField se estirará al ancho del Container (400)
                    ft.Row([txt_cantidad_ajuste], alignment=ft.MainAxisAlignment.CENTER),
                ], tight=True, spacing=15),
            ),
            actions=[
                ft.ElevatedButton("CONFIRMAR", bgcolor="#004d40", color="white", on_click=guardar_ajuste_db),
                ft.TextButton("CANCELAR", style=ft.ButtonStyle(color="#c62828"), on_click=lambda _: setattr(dlg_ajuste, "open", False) or page.update())
            ]
        )
        page.overlay.append(dlg_ajuste)
        dlg_ajuste.open = True
        page.update()

    def ejecutar_filtro(e=None):
        state["pagina"] = 1
        cargar_datos()

    def cargar_datos():
        try:
            busqueda = txt_busqueda.value.strip() if txt_busqueda.value else ""
            categoria = drop_categoria.value
            offset = (state["pagina"] - 1) * state["por_pagina"]

            productos, total_prods = obtener_inventario_paginado(
                user_id, busqueda, categoria, state["por_pagina"], offset
            )

            total_paginas = (total_prods + state["por_pagina"] - 1) // state["por_pagina"]

            tabla.rows.clear()
            
            if total_prods == 0:
                capa_mensaje.visible = True
                row_paginacion.visible = False
            else:
                capa_mensaje.visible = False
                row_paginacion.visible = True
                for p in productos:
                    tabla.rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(p['codigo_barra'] or "N/A", color="black")),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(p['nombre_producto'], color="black", no_wrap=False),
                                    width=280, 
                                    padding=ft.padding.only(top=5, bottom=5)
                                )
                            ),
                            ft.DataCell(ft.Text(p['categoria'] or "S/C", color="black")),
                            ft.DataCell(ft.Text(str(p['unidades_por_caja']), color="black")),
                            ft.DataCell(ft.Text(f"$ {p['precio_costo_total']:.2f}", color="black")),
                            ft.DataCell(ft.Text(f"$ {p['precio_venta']:.2f}", color="black")),
                            ft.DataCell(ft.Text(str(p['cantidad_unidades']), color="red" if p['cantidad_unidades'] <= 5 else "black", weight="bold")),
                            ft.DataCell(
                                ft.TextButton(
                                    content=ft.Text("AJUSTAR", color="#00897b", weight="bold"),
                                    on_click=lambda _, pid=p['id'], nom=p['nombre_producto'], stk=p['cantidad_unidades']: abrir_ajuste_stock(pid, nom, stk)
                                )
                            ),
                        ])
                    )

            txt_info_paginacion.value = f"Página {state['pagina']} de {max(1, total_paginas)} (Total: {total_prods})"
            btn_prev.disabled = state["pagina"] == 1
            btn_next.disabled = state["pagina"] >= total_paginas
            page.update()
        except Exception as ex:
            print(f"Error detallado en cargar_datos: {ex}")

    # --- COMPONENTES UI ---
    txt_busqueda = ft.TextField(label="Buscar producto o código...", expand=True, on_change=ejecutar_filtro, **estilo_campo)
    
    drop_categoria = ft.Dropdown(
        label="Categoría", width=220, value="Todos",
        label_style=ft.TextStyle(color="#004d40", weight="bold"),
        text_style=ft.TextStyle(color="black"),
        options=[ft.dropdown.Option(x) for x in ["Todos", "Papelería", "Bisutería", "Hogar", "Confitería", "Plásticos", "Quincallería", "Dulces"]]
    )
    
    btn_filtrar = ft.ElevatedButton("BUSCAR", bgcolor="#004d40", color="white", height=50, on_click=ejecutar_filtro)

    barra_filtros = ft.Container(
        content=ft.Row(controls=[txt_busqueda, drop_categoria, btn_filtrar], spacing=15),
        bgcolor="white", padding=20, border_radius=15,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=12, color="#22000000", offset=ft.Offset(0, 4))
    )

    tabla = ft.DataTable(
        heading_row_color="#004d40",
        column_spacing=20,
        data_row_max_height=float('inf'), 
        columns=[
            ft.DataColumn(ft.Text("CÓDIGO", color="white", weight="bold")),
            ft.DataColumn(ft.Text("NOMBRE", color="white", weight="bold")),
            ft.DataColumn(ft.Text("CATEGORÍA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("UND. CAJA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("COSTO T.", color="white", weight="bold")),
            ft.DataColumn(ft.Text("P. VENTA", color="white", weight="bold")),
            ft.DataColumn(ft.Text("STOCK", color="white", weight="bold")),
            ft.DataColumn(ft.Text("ACCIONES", color="white", weight="bold")),
        ],
    )

    btn_prev = ft.ElevatedButton("ANTERIOR", on_click=lambda _: nav_ant(), bgcolor="#004d40", color="white")
    btn_next = ft.ElevatedButton("SIGUIENTE", on_click=lambda _: nav_sig(), bgcolor="#004d40", color="white")
    txt_info_paginacion = ft.Text(color="black", weight="bold")
    row_paginacion = ft.Row([btn_prev, ft.Container(txt_info_paginacion, padding=10), btn_next], alignment=ft.MainAxisAlignment.CENTER)

    def nav_ant():
        if state["pagina"] > 1: state["pagina"] -= 1; cargar_datos()
    def nav_sig():
        state["pagina"] += 1; cargar_datos()

    capa_mensaje = ft.Container(
        content=ft.Column([
            ft.Text("( ! )", size=40, color="grey", weight="bold"),
            ft.Text("No se encontraron resultados.", size=16, color="grey", weight="bold")
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.Alignment(0, 0), visible=False,
    )

    contenedor_tabla = ft.Container(
        content=ft.Column([
            ft.Stack([
                ft.Column([tabla], scroll=ft.ScrollMode.ALWAYS, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                capa_mensaje
            ], expand=True),
            ft.Divider(height=1, color="black12"),
            ft.Container(content=row_paginacion, padding=10)
        ], spacing=0),
        bgcolor="white", border_radius=15, expand=True, border=ft.border.all(1, "#E0E0E0"),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=12, color="#11000000", offset=ft.Offset(0, 2))
    )

    cargar_datos()

    return ft.Column([
        ft.Text("Inventario General", size=24, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=1, thickness=1),
        barra_filtros, 
        contenedor_tabla
    ], spacing=15, expand=True)