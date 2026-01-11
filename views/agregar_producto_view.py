import flet as ft
from data.database import insertar_producto, buscar_productos, actualizar_producto

def agregar_producto_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    
    # --- ESTILOS DE ALTO CONTRASTE ---
    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="black", weight="bold"),
        "border_color": "#004d40",
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
    }

    # --- VARIABLES DE ESTADO ---
    producto_seleccionado_id = None

    # --- CAMPOS DEL FORMULARIO ---
    txt_codigo = ft.TextField(label="Código de Barras", **estilo_campo)
    txt_nombre = ft.TextField(label="Nombre del Producto", expand=True, **estilo_campo)
    txt_marca = ft.TextField(label="Marca", **estilo_campo)
    txt_categoria = ft.TextField(label="Categoría", **estilo_campo)
    
    def calcular_precio_venta(e):
        try:
            costo = float(txt_costo.value or 0)
            porc = float(txt_porcentaje.value or 0)
            if costo > 0:
                txt_venta.value = str(round(costo + (costo * porc / 100), 2))
            page.update()
        except: pass

    def calcular_porcentaje(e):
        try:
            costo = float(txt_costo.value or 0)
            venta = float(txt_venta.value or 0)
            if costo > 0:
                txt_porcentaje.value = str(round(((venta - costo) / costo) * 100, 2))
            page.update()
        except: pass

    txt_costo = ft.TextField(label="Costo", value="0", width=150, on_change=calcular_precio_venta, **estilo_campo)
    txt_porcentaje = ft.TextField(label="% Ganancia", value="0", width=150, on_change=calcular_precio_venta, **estilo_campo)
    txt_venta = ft.TextField(label="Precio Venta", value="0", width=150, on_change=calcular_porcentaje, **estilo_campo)
    txt_cantidad_nueva = ft.TextField(label="Nuevo Stock (Suma)", value="0", width=150, **estilo_campo)

    # --- COMPONENTES DE BÚSQUEDA ---
    tabla_busqueda = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Código", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Nombre", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Acción", color="black", weight="bold")),
        ],
        rows=[]
    )

    def seleccionar_para_editar(prod):
        nonlocal producto_seleccionado_id
        producto_seleccionado_id = prod['id']
        txt_codigo.value = prod['codigo_barra']
        txt_nombre.value = prod['nombre_producto']
        txt_marca.value = prod['marca_producto']
        txt_categoria.value = prod['categoria']
        txt_costo.value = str(prod['precio_costo'])
        txt_porcentaje.value = str(prod['porcentaje'])
        txt_venta.value = str(prod['precio_venta'])
        txt_cantidad_nueva.value = "0" 
        
        container_principal.content = layout_formulario
        page.update()

    def realizar_busqueda(e):
        if len(txt_buscador.value) < 1:
            tabla_busqueda.rows = []
        else:
            resultados = buscar_productos(user_id, txt_buscador.value)
            tabla_busqueda.rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p['codigo_barra'], color="black")),
                    ft.DataCell(ft.Text(p['nombre_producto'], color="black")),
                    ft.DataCell(
                        ft.ElevatedButton(
                            "MODIFICAR", 
                            color="white",
                            bgcolor="#00897b",
                            on_click=lambda _, p=p: seleccionar_para_editar(p)
                        )
                    ),
                ]) for p in resultados
            ]
        page.update()

    txt_buscador = ft.TextField(
        label="Buscar producto por nombre o código...", 
        on_change=realizar_busqueda, 
        expand=True, 
        **estilo_campo
    )

    # --- ACCIONES ---
    def guardar_click(e):
        if not txt_nombre.value:
            txt_nombre.error_text = "Obligatorio"
            page.update()
            return

        datos_form = (
            txt_codigo.value, txt_nombre.value, float(txt_costo.value or 0),
            float(txt_porcentaje.value or 0), float(txt_venta.value or 0),
            int(txt_cantidad_nueva.value or 0), txt_marca.value, txt_categoria.value
        )
        
        if producto_seleccionado_id:
            exito = actualizar_producto(producto_seleccionado_id, datos_form)
        else:
            datos_db = (user_id, txt_codigo.value, txt_nombre.value, "Unidad", 
                        float(txt_costo.value or 0), float(txt_porcentaje.value or 0), 
                        float(txt_venta.value or 0), int(txt_cantidad_nueva.value or 0), 
                        txt_marca.value, txt_categoria.value)
            exito = insertar_producto(datos_db)

        if exito:
            page.snack_bar = ft.SnackBar(ft.Text("¡Operación realizada con éxito!"), bgcolor="#004d40")
            page.snack_bar.open = True
            volver_a_busqueda(None)

    def volver_a_busqueda(e):
        nonlocal producto_seleccionado_id
        producto_seleccionado_id = None
        txt_buscador.value = ""
        tabla_busqueda.rows = []
        container_principal.content = layout_busqueda
        page.update()

    # --- LAYOUTS ---
    layout_busqueda = ft.Column([
        ft.Row([
            txt_buscador,
            ft.ElevatedButton(
                "NUEVO PRODUCTO", 
                bgcolor="#004d40", 
                color="white", 
                height=50,
                on_click=lambda _: seleccionar_para_editar({
                    'id':None, 'codigo_barra':'', 'nombre_producto':'', 
                    'marca_producto':'', 'categoria':'', 'precio_costo':0, 
                    'porcentaje':0, 'precio_venta':0})
            )
        ]),
        ft.Text("Resultados de búsqueda:", color="black", weight="bold"),
        tabla_busqueda
    ])

    layout_formulario = ft.Column([
        ft.Row([
            ft.Text("AGREGAR PRODUCTO", size=22, weight="bold", color="black"),
            # Botón de volver a la derecha con color visible (Rojo oscuro/claro)
            ft.Container(expand=True),
            ft.ElevatedButton(
                "CANCELAR / VOLVER", 
                bgcolor="#c62828", 
                color="white",
                on_click=volver_a_busqueda
            ), 
        ]),
        ft.Divider(color="black12"),
        ft.Row([txt_codigo, txt_nombre]),
        ft.Row([txt_marca, txt_categoria]),
        ft.Row([txt_costo, txt_porcentaje, txt_venta, txt_cantidad_nueva]),
        ft.Row([
            ft.ElevatedButton(
                "GUARDAR DATOS", 
                bgcolor="#004d40", 
                color="white", 
                height=50,
                on_click=guardar_click
            )
        ], alignment=ft.MainAxisAlignment.END)
    ], spacing=20)

    container_principal = ft.Container(content=layout_busqueda)
    
    return ft.Column([
        ft.Text("GESTOR DE PRODUCTOS", size=28, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=2),
        container_principal
    ], spacing=20)