import flet as ft
from data.database import insertar_producto, buscar_productos, actualizar_producto

def agregar_producto_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    
    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="black", weight="bold"),
        "border_color": "#004d40",
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
    }

    producto_seleccionado_id = None

    # --- CAMPOS DEL FORMULARIO ---
    txt_codigo = ft.TextField(label="Código de Barras", **estilo_campo)
    txt_nombre = ft.TextField(label="Nombre del Producto", expand=True, **estilo_campo)
    
    # --- LÓGICA DE CÁLCULO DE UNIDADES ---
    def calcular_unidades_totales(e):
        try:
            cajas = int(txt_cajas_recibidas.value if txt_cajas_recibidas.value else 0)
            u_por_caja = int(txt_unidades_caja.value if txt_unidades_caja.value else 1)
            txt_unidades_nuevas.value = str(cajas * u_por_caja)
            page.update()
        except ValueError:
            txt_unidades_nuevas.value = "0"
            page.update()

    txt_unidades_caja = ft.TextField(label="Unidades por Caja", value="1", width=180, on_change=calcular_unidades_totales, **estilo_campo)
    txt_cajas_recibidas = ft.TextField(label="Cantidad de Cajas", value="0", width=180, on_change=calcular_unidades_totales, **estilo_campo)
    txt_unidades_nuevas = ft.TextField(label="Total Unidades a Cargar", value="0", read_only=True, width=220, bgcolor="#f0f0f0", **estilo_campo)

    # --- LÓGICA DE PRECIOS BIDIRECCIONAL ---
    def recalcular_precios(e):
        try:
            costo_base = float(txt_costo_base.value or 0)
            p_transporte = float(txt_p_transporte.value or 0)
            costo_total = float(txt_costo_total.value or 0)
            p_venta = float(txt_p_venta.value or 0)
            venta_final = float(txt_venta_final.value or 0)

            # 1. Lógica para COSTO TOTAL / TRANSPORTE
            if e.control in [txt_costo_base, txt_p_transporte]:
                costo_total = costo_base + (costo_base * (p_transporte / 100))
                txt_costo_total.value = str(round(costo_total, 2))
            
            elif e.control == txt_costo_total:
                if costo_base > 0:
                    p_transporte = ((costo_total - costo_base) / costo_base) * 100
                    txt_p_transporte.value = str(round(p_transporte, 2))
                else:
                    txt_p_transporte.value = "0"

            # Re-leer costo_total actualizado para los siguientes cálculos
            costo_total = float(txt_costo_total.value or 0)

            # 2. Lógica para VENTA FINAL / GANANCIA
            if e.control in [txt_p_venta, txt_costo_base, txt_p_transporte, txt_costo_total]:
                venta_final = costo_total + (costo_total * (p_venta / 100))
                txt_venta_final.value = str(round(venta_final, 2))
            
            elif e.control == txt_venta_final:
                if costo_total > 0:
                    p_venta = ((venta_final - costo_total) / costo_total) * 100
                    txt_p_venta.value = str(round(p_venta, 2))
                else:
                    txt_p_venta.value = "0"

            page.update()
        except:
            pass

    txt_costo_base = ft.TextField(label="Precio Costo", value="0", on_change=recalcular_precios, **estilo_campo)
    txt_p_transporte = ft.TextField(label="% Transporte", value="0", on_change=recalcular_precios, **estilo_campo)
    
    # Estos campos ya NO son read_only
    txt_costo_total = ft.TextField(label="Costo Total", value="0", on_change=recalcular_precios, bgcolor="#E8F5E9", **estilo_campo)
    txt_p_venta = ft.TextField(label="% Ganancia Venta", value="0", on_change=recalcular_precios, **estilo_campo)
    txt_venta_final = ft.TextField(label="Precio Venta Final", value="0", on_change=recalcular_precios, **estilo_campo)
    
    txt_marca = ft.TextField(label="Marca", **estilo_campo)
    txt_categoria = ft.TextField(label="Categoría", **estilo_campo)

    lista_resultados = ft.ListView(expand=True, spacing=10, padding=10)

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
        
        txt_cajas_recibidas.value = "0"
        txt_unidades_nuevas.value = "0"
        txt_marca.value = str(prod['marca_producto'] or "")
        txt_categoria.value = str(prod['categoria'] or "")
        
        container_principal.content = layout_formulario
        page.update()

    def realizar_busqueda(e):
        lista_resultados.controls.clear()
        if len(txt_buscador.value) >= 1:
            resultados = buscar_productos(user_id, txt_buscador.value)
            for p in resultados:
                lista_resultados.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(p['codigo_barra'], width=150, color="black", weight="bold"),
                            ft.Text(p['nombre_producto'], expand=True, color="black"),
                            ft.ElevatedButton(
                                "MODIFICAR", 
                                bgcolor="#00897b", 
                                color="white", 
                                on_click=lambda _, p=p: seleccionar_para_editar(p)
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        border=ft.border.only(bottom=ft.border.BorderSide(1, "black12"))
                    )
                )
        page.update()

    txt_buscador = ft.TextField(label="Buscar por nombre o código...", on_change=realizar_busqueda, expand=True, **estilo_campo)

    def guardar_click(e):
        if not txt_nombre.value:
            txt_nombre.error_text = "Nombre obligatorio"
            page.update()
            return
        
        datos_db = (
            txt_codigo.value, txt_nombre.value, int(txt_unidades_caja.value or 1),
            float(txt_costo_base.value or 0), float(txt_p_transporte.value or 0),
            float(txt_costo_total.value or 0), float(txt_p_venta.value or 0),
            float(txt_venta_final.value or 0), int(txt_unidades_nuevas.value or 0),
            txt_marca.value, txt_categoria.value
        )
        
        if producto_seleccionado_id:
            exito = actualizar_producto(producto_seleccionado_id, datos_db)
        else:
            exito = insertar_producto((user_id,) + datos_db)

        if exito:
            page.snack_bar = ft.SnackBar(ft.Text("¡Operación exitosa!"), bgcolor="#004d40")
            page.snack_bar.open = True
            volver_a_busqueda(None)

    def volver_a_busqueda(e):
        nonlocal producto_seleccionado_id
        producto_seleccionado_id = None
        txt_buscador.value = ""
        lista_resultados.controls.clear()
        container_principal.content = layout_busqueda
        page.update()

    # --- LAYOUTS ---
    layout_busqueda = ft.Column([
        ft.Row([
            txt_buscador,
            ft.ElevatedButton("NUEVO PRODUCTO", bgcolor="#004d40", color="white", height=50, 
                on_click=lambda _: seleccionar_para_editar({
                    'id':None, 'codigo_barra':'', 'nombre_producto':'', 'unidades_por_caja':1,
                    'precio_costo':0, 'porcentaje_transporte':0, 'precio_costo_total':0, 
                    'porcentaje_venta':0, 'precio_venta':0, 'marca_producto':'', 'categoria':''
                }))
        ]),
        ft.Container(
            content=ft.Row([
                ft.Text("CÓDIGO", width=150, color="black", weight="bold"),
                ft.Text("NOMBRE DEL PRODUCTO", expand=True, color="black", weight="bold"),
                ft.Text("ACCIÓN", width=100, color="black", weight="bold", text_align=ft.TextAlign.RIGHT),
            ]),
            padding=ft.padding.only(left=10, right=25)
        ),
        ft.Divider(color="black12"),
        lista_resultados
    ], expand=True)

    layout_formulario = ft.Column([
        ft.Row([
            ft.Text("DETALLES DE ENTRADA", size=22, weight="bold", color="black"),
            ft.Container(expand=True),
            ft.ElevatedButton("CANCELAR", bgcolor="#c62828", color="white", on_click=volver_a_busqueda), 
        ]),
        ft.Divider(color="black12"),
        ft.Row([txt_codigo, txt_nombre]),
        ft.Row([txt_marca, txt_categoria]),
        
        # SECCIÓN DE INVENTARIO
        ft.Container(
            content=ft.Column([
                ft.Text("Gestión de Unidades y Cajas", weight="bold", color="#004d40", size=16),
                ft.Row([txt_unidades_caja, txt_cajas_recibidas, txt_unidades_nuevas], spacing=20),
            ]),
            padding=10, bgcolor="#f9f9f9", border_radius=10
        ),
        
        # SECCIÓN DE COSTOS (Actualizada)
        ft.Container(
            content=ft.Column([
                ft.Text("Costos y Ganancias", weight="bold", color="#004d40", size=16),
                ft.Row([txt_costo_base, txt_p_transporte, txt_costo_total], spacing=20),
                ft.Row([txt_p_venta, txt_venta_final], spacing=20),
            ]),
            padding=10, bgcolor="#f9f9f9", border_radius=10
        ),

        ft.Row([
            ft.ElevatedButton(
                "GUARDAR PRODUCTO", 
                bgcolor="#004d40", 
                color="white", 
                height=50, 
                on_click=guardar_click
            )
        ], alignment=ft.MainAxisAlignment.END)
    ], spacing=15, scroll=ft.ScrollMode.ALWAYS)

    container_principal = ft.Container(content=layout_busqueda, expand=True)
    
    return ft.Column([
        ft.Text("GESTOR DE PRODUCTOS", size=28, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=2),
        container_principal
    ], spacing=20, expand=True)