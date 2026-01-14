import flet as ft
from data.productos import insertar_producto, buscar_productos, actualizar_producto

def agregar_producto_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    
    # --- FUNCIÓN DE MENSAJES ---
    def mostrar_mensaje(texto, color="#c62828", color_text="white"):
        snack = ft.SnackBar(ft.Text(texto, color=color_text), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="black", weight="bold"),
        "border_color": "#004d40",
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
    }

    producto_seleccionado_id = None

    # --- CAMPOS DEL FORMULARIO ---
    txt_codigo = ft.TextField(label="Código de Barras", bgcolor="white", **estilo_campo)
    txt_nombre = ft.TextField(label="Nombre del Producto", expand=True, bgcolor="white", **estilo_campo)
    
    drop_categoria = ft.Dropdown(
        label="Categoría",
        **estilo_campo,
        options=[
            ft.dropdown.Option("Papelería"), ft.dropdown.Option("Bisutería"),
            ft.dropdown.Option("Hogar"), ft.dropdown.Option("Confitería"),
            ft.dropdown.Option("Plásticos"), ft.dropdown.Option("Quincallería"),
            ft.dropdown.Option("Dulces"), ft.dropdown.Option("Otros"),
        ],
        width=300,
    )

    # --- LÓGICA DE PRECIOS CON VALIDACIÓN ---
    def recalcular_precios(e):
        try:
            nombres_campos = {
                txt_costo_por_caja: "Costo por Caja",
                txt_unidades_caja: "Unidades por Caja",
                txt_costo_base: "Precio Costo Unitario",
                txt_p_transporte: "% Transporte",
                txt_costo_total: "Costo Total",
                txt_p_venta: "% Ganancia",
                txt_venta_final: "Precio Venta Final"
            }

            if e.control.value and not e.control.value.replace('.', '', 1).isdigit():
                mostrar_mensaje(f"Error: El campo '{nombres_campos[e.control]}' solo acepta números.")
                e.control.value = "0"
                page.update()
                return

            costo_caja = float(txt_costo_por_caja.value or 0)
            u_caja = int(txt_unidades_caja.value or 1)
            
            if costo_caja > 0:
                txt_costo_base.value = str(round(costo_caja / u_caja, 2))
            
            costo_base = float(txt_costo_base.value or 0)
            p_transporte = float(txt_p_transporte.value or 0)
            
            if e.control in [txt_costo_base, txt_p_transporte, txt_costo_por_caja, txt_unidades_caja]:
                costo_total = costo_base + (costo_base * (p_transporte / 100))
                txt_costo_total.value = str(round(costo_total, 2))
            
            elif e.control == txt_costo_total:
                costo_total = float(txt_costo_total.value or 0)
                if costo_base > 0:
                    p_transporte = ((costo_total - costo_base) / costo_base) * 100
                    txt_p_transporte.value = str(round(p_transporte, 2))

            costo_total = float(txt_costo_total.value or 0)
            p_venta = float(txt_p_venta.value or 0)
            
            if e.control in [txt_p_venta, txt_costo_base, txt_p_transporte, txt_costo_total, txt_costo_por_caja, txt_unidades_caja]:
                venta_final = costo_total + (costo_total * (p_venta / 100))
                txt_venta_final.value = str(round(venta_final, 2))
            
            elif e.control == txt_venta_final:
                venta_final = float(txt_venta_final.value or 0)
                if costo_total > 0:
                    p_venta = ((venta_final - costo_total) / costo_total) * 100
                    txt_p_venta.value = str(round(p_venta, 2))

            page.update()
        except ValueError:
            mostrar_mensaje("Error: Por favor ingresa un formato numérico válido (ej: 10.50)")

    def manejar_cambio_unidades(e):
        try:
            if e.control.value and not e.control.value.isdigit():
                mostrar_mensaje(f"Error: El campo Unidades/Cajas debe ser un número entero.")
                e.control.value = "0"
                page.update()
                return

            cajas = int(txt_cajas_recibidas.value if txt_cajas_recibidas.value else 0)
            u_por_caja = int(txt_unidades_caja.value if txt_unidades_caja.value else 1)
            txt_unidades_nuevas.value = str(cajas * u_por_caja)
            
            if txt_costo_por_caja.value and float(txt_costo_por_caja.value) > 0:
                recalcular_precios(e)
            page.update()
        except:
            pass

    # --- CAMPOS DE ENTRADA ---
    txt_unidades_caja = ft.TextField(label="Unidades por Caja", value="1", width=180, on_change=manejar_cambio_unidades, bgcolor="white", **estilo_campo)
    txt_cajas_recibidas = ft.TextField(label="Cantidad de Cajas", value="0", width=180, on_change=manejar_cambio_unidades, bgcolor="white", **estilo_campo)
    txt_unidades_nuevas = ft.TextField(label="Total Unidades a Cargar", value="0", read_only=True, width=220, bgcolor="#EEEEEE", **estilo_campo)

    txt_costo_por_caja = ft.TextField(label="Costo por Caja ($)", on_change=recalcular_precios, bgcolor="#FFF3E0", **estilo_campo)
    txt_costo_base = ft.TextField(label="Precio Costo Unit. ($)", value="0", on_change=recalcular_precios, bgcolor="white", **estilo_campo)
    txt_p_transporte = ft.TextField(label="% Transporte", value="0", on_change=recalcular_precios, bgcolor="white", **estilo_campo)
    txt_costo_total = ft.TextField(label="Costo Total ($)", value="0", on_change=recalcular_precios, bgcolor="#E8F5E9", **estilo_campo)
    txt_p_venta = ft.TextField(label="% Ganancia Venta", value="0", on_change=recalcular_precios, bgcolor="white", **estilo_campo)
    txt_venta_final = ft.TextField(label="Precio Venta Final ($)", value="0", on_change=recalcular_precios, bgcolor="white", **estilo_campo)
    
    txt_marca = ft.TextField(label="Marca", bgcolor="white", **estilo_campo)
    
    lista_resultados = ft.ListView(expand=True, spacing=0)

    # --- LÓGICA DE BÚSQUEDA SIN ICONOS ---
    def realizar_busqueda(e):
        lista_resultados.controls.clear()
        termino = txt_buscador.value.strip()

        if not termino:
            # Mensaje Inicial (Solo texto)
            lista_resultados.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("( ? )", size=40, weight="bold", color="#BDBDBD"),
                        ft.Text("Busca un producto para comenzar...", color="#9E9E9E", size=16)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    margin=ft.margin.only(top=40)
                )
            )
        else:
            resultados = buscar_productos(user_id, termino)
            if not resultados:
                # Mensaje de "No se encontraron resultados" (Solo texto como en la imagen)
                lista_resultados.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("( ! )", size=40, weight="bold", color="#BDBDBD"),
                            ft.Text("No se encontraron resultados.", color="#9E9E9E", size=16)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        margin=ft.margin.only(top=40)
                    )
                )
            else:
                for p in resultados:
                    lista_resultados.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(p['codigo_barra'] or "S/C", width=150, color="black", weight="bold"),
                                ft.Text(p['nombre_producto'], expand=True, color="black"),
                                ft.ElevatedButton(
                                    "MODIFICAR", bgcolor="#00897b", color="white", 
                                    on_click=lambda _, p=p: seleccionar_para_editar(p)
                                ),
                            ]),
                            padding=ft.padding.symmetric(vertical=8, horizontal=15),
                            border=ft.border.only(bottom=ft.border.BorderSide(1, "#EEEEEE"))
                        )
                    )
        page.update()

    def seleccionar_para_editar(prod):
        nonlocal producto_seleccionado_id
        producto_seleccionado_id = prod['id']
        txt_codigo.value = str(prod['codigo_barra'] or "")
        txt_nombre.value = str(prod['nombre_producto'] or "")
        txt_unidades_caja.value = str(prod['unidades_por_caja'])
        txt_costo_base.value = str(prod['precio_costo'])
        txt_p_transporte.value = str(prod['porcentaje_transporte'])
        txt_costo_total.value = str(prod['precio_costo_total'])
        txt_p_venta.value = str(prod['porcentaje_venta'])
        txt_venta_final.value = str(prod['precio_venta'])
        txt_marca.value = str(prod['marca_producto'] or "")
        drop_categoria.value = str(prod['categoria']) if prod['categoria'] else None
        
        txt_costo_por_caja.value = ""
        txt_cajas_recibidas.value = "0"
        txt_unidades_nuevas.value = "0"
        
        container_principal.content = layout_formulario
        page.update()

    txt_buscador = ft.TextField(label="Buscar producto...", on_change=realizar_busqueda, expand=True, bgcolor="white", **estilo_campo)

    def guardar_click(e):
        if not txt_nombre.value:
            txt_nombre.error_text = "Nombre obligatorio"; page.update(); return
        try:
            datos_db = (
                txt_codigo.value, txt_nombre.value, int(txt_unidades_caja.value or 1),
                float(txt_costo_base.value or 0), float(txt_p_transporte.value or 0),
                float(txt_costo_total.value or 0), float(txt_p_venta.value or 0),
                float(txt_venta_final.value or 0), int(txt_unidades_nuevas.value or 0),
                txt_marca.value, drop_categoria.value
            )
            if producto_seleccionado_id:
                exito = actualizar_producto(producto_seleccionado_id, datos_db)
            else:
                exito = insertar_producto((user_id,) + datos_db)

            if exito:
                mostrar_mensaje("¡Producto guardado!", color="#004d40")
                volver_a_busqueda(None)
        except Exception as ex:
            mostrar_mensaje(f"Error: {ex}")

    def volver_a_busqueda(e):
        nonlocal producto_seleccionado_id
        producto_seleccionado_id = None
        txt_buscador.value = ""
        realizar_busqueda(None)
        container_principal.content = layout_busqueda
        page.update()

    # --- DISEÑO VISTA BÚSQUEDA ---
    layout_busqueda = ft.Column([
        ft.Container(
            content=ft.Row([
                txt_buscador,
                ft.ElevatedButton("NUEVO PRODUCTO", bgcolor="#004d40", color="white", height=50, 
                    on_click=lambda _: seleccionar_para_editar({
                        'id':None, 'codigo_barra':'', 'nombre_producto':'', 'unidades_por_caja':1,
                        'precio_costo':0, 'porcentaje_transporte':0, 'precio_costo_total':0, 
                        'porcentaje_venta':0, 'precio_venta':0, 'marca_producto':'', 'categoria':None
                    }))
            ]),
            bgcolor="white", padding=20, border_radius=15,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=12, color="#22000000", offset=ft.Offset(0, 4))
        ),
        ft.Container(
            content=ft.Column([
                ft.Container(content=ft.Row([
                    ft.Text("CÓDIGO", width=150, color="#004d40", weight="bold"),
                    ft.Text("NOMBRE DEL PRODUCTO", expand=True, color="#004d40", weight="bold"),
                    ft.Text("ACCIÓN", width=120, color="#004d40", weight="bold", text_align="center"),
                ]), padding=ft.padding.only(left=15, right=15, top=20, bottom=10)),
                ft.Divider(height=1, color="#EEEEEE"),
                lista_resultados
            ], spacing=0),
            bgcolor="white", border_radius=15, expand=True, border=ft.border.all(1, "#E0E0E0")
        )
    ], expand=True, spacing=15)

    # --- DISEÑO VISTA FORMULARIO ---
    layout_formulario = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("DATOS DEL PRODUCTO", size=22, weight="bold", color="black"),
                ft.Container(expand=True),
                ft.ElevatedButton("CANCELAR", bgcolor="#c62828", color="white", on_click=volver_a_busqueda), 
            ]),
            ft.Divider(color="black12"),
            ft.Row([txt_codigo, txt_nombre]),
            ft.Row([txt_marca, drop_categoria]),
            ft.Text("Inventario", weight="bold", color="#004d40", size=16),
            ft.Row([txt_unidades_caja, txt_cajas_recibidas, txt_unidades_nuevas], spacing=20),
            ft.Divider(color="black12"),
            ft.Text("Precios y Costos", weight="bold", color="#004d40", size=16),
            ft.Row([txt_costo_por_caja, ft.Text("← Use este campo si compró por caja", size=12, italic=True)]),
            ft.Row([txt_costo_base, txt_p_transporte, txt_costo_total], spacing=20),
            ft.Row([txt_p_venta, txt_venta_final], spacing=20),
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton("GUARDAR PRODUCTO EN INVENTARIO", bgcolor="#004d40", color="white", height=55, width=350, on_click=guardar_click)
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=20, scroll=ft.ScrollMode.ADAPTIVE),
        bgcolor="white", padding=30, border_radius=15, expand=True,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color="#25000000", offset=ft.Offset(0, 5))
    )

    realizar_busqueda(None)
    container_principal = ft.Container(content=layout_busqueda, expand=True)
    
    return ft.Column([
        ft.Text("Gestor De Productos", size=24, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=2),
        container_principal
    ], spacing=15, expand=True)