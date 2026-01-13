import flet as ft
from data.database import buscar_productos, buscar_cliente_por_rif, guardar_factura_completa
from services.pdf_service import generar_factura_pdf
from services.email_service import enviar_factura_email
import os

def factura_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    carrito = []
    controles_stock_visibles = {}

    def mostrar_mensaje(texto, color="#b71c1c"):
        snack = ft.SnackBar(ft.Text(texto, color="white"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    COLOR_PRIMARIO = "#004d40"

    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color=COLOR_PRIMARIO, weight="bold"),
        "border_color": COLOR_PRIMARIO,
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
        "bgcolor": "#FFFFFF"
    }

    # --- CAMPOS DEL CLIENTE ---
    txt_cliente_id = ft.TextField(label="Cédula / RIF", **estilo_campo)
    txt_cliente_nombre = ft.TextField(label="Nombre / Razón Social", **estilo_campo, expand=True)
    txt_cliente_dir = ft.TextField(label="Dirección", **estilo_campo, expand=True)
    txt_cliente_zona = ft.TextField(label="Zona", **estilo_campo)
    txt_cliente_email = ft.TextField(label="Correo (Opcional)", **estilo_campo, expand=True)

    # --- TABLA Y RESUMEN ---
    txt_total_pago = ft.Text("Total a Pagar: 0.00$", size=22, weight="bold", color=COLOR_PRIMARIO)
    
    tabla_carrito = ft.DataTable(
        column_spacing=15,
        columns=[
            ft.DataColumn(ft.Container(ft.Text("Producto", color="black", weight="bold"), width=120)),
            ft.DataColumn(ft.Text("Cant.", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Empaque", color="black", weight="bold")),
            ft.DataColumn(ft.Container(ft.Text("Precio", color="black", weight="bold"), width=70)),
            ft.DataColumn(ft.Container(ft.Text("Subtotal", color="black", weight="bold"), width=80)),
            ft.DataColumn(ft.Text("Acción", color="black", weight="bold")),
        ],
        rows=[]
    )

    def actualizar_tabla():
        tabla_carrito.rows.clear()
        total = sum(item['subtotal'] for item in carrito)
        for i, item in enumerate(carrito):
            tabla_carrito.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Container(content=ft.Text(item['nombre'], color="black"), width=120)),
                    ft.DataCell(ft.Text(str(item['cantidad']), color="black")),
                    ft.DataCell(ft.Text(item['tipo'], color="black")),
                    ft.DataCell(ft.Text(f"{item['precio_unitario']:.2f}$", color="black")),
                    ft.DataCell(ft.Text(f"{item['subtotal']:.2f}$", color="black")),
                    ft.DataCell(ft.TextButton("Quitar", on_click=lambda _, idx=i: eliminar_item(idx), style=ft.ButtonStyle(color="red"))),
                ])
            )
        txt_total_pago.value = f"Total a Pagar: {total:.2f}$"
        page.update()

    def eliminar_item(idx):
        item_removido = carrito.pop(idx)
        if item_removido['id'] in controles_stock_visibles:
            txt_obj, p_data = controles_stock_visibles[item_removido['id']]
            en_carrito_restante = sum(it['unidades_totales'] for it in carrito if it['id'] == item_removido['id'])
            txt_obj.value = f"Stock: {p_data['cantidad_unidades'] - en_carrito_restante} | Precio: {p_data['precio_venta']}$"
        actualizar_tabla()

    def agregar_al_carrito(prod, input_control, type_control):
        try:
            cantidad_ingresada = int(input_control.value)
            if cantidad_ingresada <= 0: return
            valor_radio = type_control.value
            tipo_legible = "Unid." if valor_radio == "und" else "Caja"
            u_por_caja = int(prod.get('unidades_por_caja') or 1)
            unidades_a_añadir = cantidad_ingresada if valor_radio == "und" else (cantidad_ingresada * u_por_caja)
            stock_disponible = int(prod['cantidad_unidades'])
            cantidad_total_en_carrito = sum(item['unidades_totales'] for item in carrito if item['id'] == prod['id'])

            if (cantidad_total_en_carrito + unidades_a_añadir) > stock_disponible:
                mostrar_mensaje(f"Stock insuficiente ({stock_disponible - cantidad_total_en_carrito} disp.)")
                return

            precio_base = float(prod['precio_venta'])
            precio_item = precio_base if valor_radio == "und" else (precio_base * u_por_caja)
            item_existente = next((item for item in carrito if item['id'] == prod['id'] and item['tipo'] == tipo_legible), None)
            
            if item_existente:
                item_existente['cantidad'] += cantidad_ingresada
                item_existente['unidades_totales'] += unidades_a_añadir
                item_existente['subtotal'] = round(item_existente['cantidad'] * item_existente['precio_unitario'], 2)
            else:
                carrito.append({
                    "id": prod['id'], "nombre": prod['nombre_producto'],
                    "cantidad": cantidad_ingresada, "tipo": tipo_legible,
                    "unidades_totales": unidades_a_añadir, "precio_unitario": precio_item,
                    "subtotal": round(precio_item * cantidad_ingresada, 2)
                })
            
            if prod['id'] in controles_stock_visibles:
                txt_obj, p_data = controles_stock_visibles[prod['id']]
                actual_en_carrito = sum(it['unidades_totales'] for it in carrito if it['id'] == prod['id'])
                txt_obj.value = f"Stock: {p_data['cantidad_unidades'] - actual_en_carrito} | Precio: {p_data['precio_venta']}$"
            actualizar_tabla()
        except: pass

    # --- BÚSQUEDA PRODUCTOS ---
    resultados_busqueda = ft.ListView(expand=True, spacing=5)
    txt_busca_prod = ft.TextField(label="Buscar producto...", on_change=lambda e: buscar_p(e), **estilo_campo, expand=True)

    def buscar_p(e):
        resultados_busqueda.controls.clear()
        if len(txt_busca_prod.value) >= 1:
            prods = buscar_productos(user_id, txt_busca_prod.value)
            for p in prods:
                p_dict = dict(p)
                en_carrito = sum(it['unidades_totales'] for it in carrito if it['id'] == p_dict['id'])
                cant_input = ft.TextField(value="1", width=60, dense=True, text_align="center", color="black", border_color=COLOR_PRIMARIO)
                
                # Texto de stock en NEGRO
                txt_stock_item = ft.Text(f"Stock: {p_dict['cantidad_unidades'] - en_carrito} | Precio: {p_dict['precio_venta']}$", size=12, color="black")
                controles_stock_visibles[p_dict['id']] = (txt_stock_item, p_dict)

                # Radio con etiquetas en NEGRO
                opcion_empaque = ft.RadioGroup(
                    content=ft.Row([
                        ft.Radio(value="und", label="UND", fill_color=COLOR_PRIMARIO, label_style=ft.TextStyle(color="black")),
                        ft.Radio(value="caja", label="CAJA", fill_color=COLOR_PRIMARIO, label_style=ft.TextStyle(color="black")),
                    ], spacing=10), value="und"
                )
                
                resultados_busqueda.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([ft.Text(p_dict['nombre_producto'], weight="bold", color="black", size=15), txt_stock_item], expand=True),
                            opcion_empaque, cant_input,
                            ft.TextButton("Añadir", on_click=lambda _, p=p_dict, c=cant_input, t=opcion_empaque: agregar_al_carrito(p, c, t), style=ft.ButtonStyle(color=COLOR_PRIMARIO))
                        ]), padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "black12")), bgcolor="#FFFFFF"
                    )
                )
        page.update()

    # --- BÚSQUEDA CLIENTES (Estilo Gestor de Productos) ---
    lista_clientes = ft.ListView(expand=True, spacing=10, scroll=ft.ScrollMode.HIDDEN)
    txt_busca_cliente = ft.TextField(label="Buscar cliente...", on_change=lambda e: realizar_busqueda_cliente(e), expand=True, **estilo_campo)

    def realizar_busqueda_cliente(e):
        lista_clientes.controls.clear()
        if len(txt_busca_cliente.value) >= 1:
            clientes = buscar_cliente_por_rif(user_id, txt_busca_cliente.value)
            for c in clientes:
                lista_clientes.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(c['cedula_rif'], width=150, color="black", weight="bold"),
                            ft.Text(c['nombre_razon'], expand=True, color="black"),
                            ft.ElevatedButton("CREAR", bgcolor="#00897b", color="white", 
                                             on_click=lambda _, cli=c: iniciar_factura_con_cliente(cli)),
                        ]), padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "black12"))
                    )
                )
        page.update()

    def iniciar_factura_con_cliente(cliente=None):
        if cliente:
            c = dict(cliente)
            txt_cliente_id.value = c['cedula_rif']; txt_cliente_nombre.value = c['nombre_razon']
            txt_cliente_dir.value = c['direccion']; txt_cliente_zona.value = c['zona']
            txt_cliente_email.value = c.get('email', "") or ""
        else:
            txt_cliente_id.value = ""; txt_cliente_nombre.value = ""; txt_cliente_dir.value = ""; txt_cliente_zona.value = ""; txt_cliente_email.value = ""
        container_principal.content = layout_formulario
        page.update()

    def volver_a_lista_clientes(e):
        carrito.clear(); actualizar_tabla()
        txt_busca_cliente.value = ""; lista_clientes.controls.clear()
        container_principal.content = layout_seleccion_cliente
        page.update()

    def procesar_factura(e):
        if not carrito or not txt_cliente_id.value:
            mostrar_mensaje("Error: Datos incompletos")
            return
        try:
            monto_total = sum(item['subtotal'] for item in carrito)
            datos_cliente = {
                "cedula_rif": txt_cliente_id.value, "nombre_razon": txt_cliente_nombre.value, 
                "direccion": txt_cliente_dir.value, "zona": txt_cliente_zona.value, "email": txt_cliente_email.value.strip()
            }
            res = guardar_factura_completa(user_id, datos_cliente, carrito, monto_total)
            if res["success"]:
                res['cliente'] = datos_cliente
                generar_factura_pdf(res, carrito)
                if datos_cliente["email"] and "@" in datos_cliente["email"]:
                    ruta_pdf = os.path.join("facturas_generadas", f"Nota_{res['numero_factura']}.pdf")
                    enviar_factura_email(datos_cliente["email"], res['numero_factura'], ruta_pdf)
                mostrar_mensaje("¡Venta Exitosa!", color="#2e7d32")
                volver_a_lista_clientes(None)
            else: mostrar_mensaje(f"Error DB: {res.get('error')}")
        except Exception as ex: mostrar_mensaje(f"Error: {ex}")

    # --- LAYOUTS ---
    layout_seleccion_cliente = ft.Column([
        ft.Row([txt_busca_cliente, ft.ElevatedButton("NUEVO CLIENTE", bgcolor=COLOR_PRIMARIO, color="white", height=50, on_click=lambda _: iniciar_factura_con_cliente(None))]),
        ft.Container(
            content=ft.Row([
                ft.Text("RIF / CÉDULA", width=150, color="black", weight="bold"),
                ft.Text("NOMBRE O RAZÓN SOCIAL", expand=True, color="black", weight="bold"),
                ft.Text("ACCIÓN", width=100, color="black", weight="bold", text_align="right"),
            ]),
            padding=ft.padding.only(left=10, right=25)
        ),
        ft.Divider(color="black12"),
        lista_clientes
    ], expand=True)

    layout_formulario = ft.Row([
        ft.Column([
            ft.Container(content=ft.Column([
                ft.Row([ft.Text("DATOS DEL CLIENTE", weight="bold", color=COLOR_PRIMARIO), ft.Container(expand=True), ft.TextButton("Cambiar", on_click=volver_a_lista_clientes)]),
                ft.Row([txt_cliente_id, txt_cliente_nombre]),
                ft.Row([txt_cliente_dir, txt_cliente_zona]),
                ft.Row([txt_cliente_email]),
            ]), padding=15, bgcolor="white", border_radius=8),
            ft.Container(content=ft.Column([
                ft.Text("AÑADIR PRODUCTOS", weight="bold", color=COLOR_PRIMARIO),
                ft.Row([txt_busca_prod]), 
                ft.Container(content=resultados_busqueda, expand=True)
            ]), padding=15, bgcolor="white", border_radius=8, expand=True),
        ], expand=1, spacing=15),
        ft.Column([
            ft.Container(content=ft.Column([
                ft.Text("RESUMEN DE VENTA", weight="bold", color=COLOR_PRIMARIO),
                ft.Divider(),
                ft.Container(content=ft.Column([tabla_carrito], scroll=ft.ScrollMode.ALWAYS), expand=True),
                ft.Divider(),
                ft.Row([txt_total_pago], alignment=ft.MainAxisAlignment.END),
                ft.Container(content=ft.ElevatedButton("GUARDAR Y GENERAR PDF", bgcolor=COLOR_PRIMARIO, color="white", height=50, on_click=procesar_factura), width=float("inf"))
            ]), padding=20, bgcolor="white", border_radius=8, expand=True)
        ], expand=1)
    ], spacing=25, expand=True)

    container_principal = ft.Container(content=layout_seleccion_cliente, expand=True)
    return ft.Column([
        ft.Text("GENERAR NOTA DE ENTREGA", size=28, weight="bold", color="#00332a"), 
        ft.Divider(color="#00332a", height=2), 
        container_principal
    ], spacing=20, expand=True)