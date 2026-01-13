import flet as ft
from data.database import buscar_productos, buscar_cliente_por_rif, guardar_factura_completa
from services.pdf_service import generar_factura_pdf
from services.email_service import enviar_factura_email
import os

def factura_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    carrito = []

    def mostrar_mensaje(texto, color="#b71c1c"):
        snack = ft.SnackBar(ft.Text(texto, color="white"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="#004d40", weight="bold"),
        "border_color": "#004d40",
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

    # --- BÚSQUEDA DE PRODUCTOS ---
    resultados_busqueda = ft.ListView(expand=True, spacing=5)
    
    def buscar_p(e):
        resultados_busqueda.controls.clear()
        if len(txt_busca_prod.value) >= 1:
            prods = buscar_productos(user_id, txt_busca_prod.value)
            for p in prods:
                cant_input = ft.TextField(
                    value="1", width=60, dense=True, text_align="center",
                    color="black", border_color="#004d40", bgcolor="#f5f5f5"
                )
                resultados_busqueda.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(p['nombre_producto'], weight="bold", color="black", size=15),
                                ft.Text(f"Stock: {p['cantidad_unidades']} | Precio: {p['precio_venta']}$", size=12, color="#212121"),
                            ], expand=True),
                            cant_input,
                            ft.TextButton("Añadir", on_click=lambda _, p=p, c=cant_input: agregar_al_carrito(p, c), style=ft.ButtonStyle(color="#004d40"))
                        ]),
                        padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "black12")), bgcolor="#FFFFFF"
                    )
                )
        page.update()

    txt_busca_prod = ft.TextField(label="Buscar producto por nombre o código...", on_change=buscar_p, **estilo_campo, expand=True)

    # --- TABLA Y LÓGICA DE CARRITO ---
    txt_total_pago = ft.Text("Total a Pagar: 0.00$", size=22, weight="bold", color="#004d40")
    tabla_carrito = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Producto", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Cant.", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Precio", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Subtotal", color="black", weight="bold")),
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
                    ft.DataCell(ft.Text(item['nombre'], color="black")),
                    ft.DataCell(ft.Text(str(item['cantidad']), color="black")),
                    ft.DataCell(ft.Text(f"{item['precio']:.2f}$", color="black")),
                    ft.DataCell(ft.Text(f"{item['subtotal']:.2f}$", color="black")),
                    ft.DataCell(ft.TextButton("Quitar", on_click=lambda _, idx=i: eliminar_item(idx))),
                ])
            )
        txt_total_pago.value = f"Total a Pagar: {total:.2f}$"
        page.update()

    def agregar_al_carrito(prod, input_control):
        try:
            cantidad_nueva = int(input_control.value)
            if cantidad_nueva <= 0: return
            stock_disponible = int(prod['cantidad_unidades'])
            cantidad_en_carrito = sum(item['cantidad'] for item in carrito if item['id'] == prod['id'])

            if (cantidad_en_carrito + cantidad_nueva) > stock_disponible:
                mostrar_mensaje(f"Error: Stock insuficiente. Solo quedan {stock_disponible} unidades.")
                return

            item_existente = next((item for item in carrito if item['id'] == prod['id']), None)
            if item_existente:
                item_existente['cantidad'] += cantidad_nueva
                item_existente['subtotal'] = round(item_existente['cantidad'] * item_existente['precio'], 2)
            else:
                subtotal = float(prod['precio_venta']) * cantidad_nueva
                carrito.append({
                    "id": prod['id'], "nombre": prod['nombre_producto'],
                    "cantidad": cantidad_nueva, "precio": float(prod['precio_venta']),
                    "subtotal": round(subtotal, 2)
                })
            
            input_control.value = "1"
            actualizar_tabla()
        except:
            mostrar_mensaje("Error: Ingrese una cantidad válida")

    def eliminar_item(idx):
        carrito.pop(idx)
        actualizar_tabla()

    def iniciar_factura_con_cliente(cliente=None):
        if cliente:
            # Convertimos sqlite3.Row a diccionario para evitar errores con .get()
            cli_dict = dict(cliente)
            txt_cliente_id.value = cli_dict['cedula_rif']
            txt_cliente_nombre.value = cli_dict['nombre_razon']
            txt_cliente_dir.value = cli_dict['direccion']
            txt_cliente_zona.value = cli_dict['zona']
            txt_cliente_email.value = cli_dict.get('email', "") if cli_dict.get('email') else ""
        else:
            txt_cliente_id.value = ""; txt_cliente_nombre.value = ""
            txt_cliente_dir.value = ""; txt_cliente_zona.value = ""
            txt_cliente_email.value = ""
            
        container_principal.content = layout_formulario
        page.update()

    def volver_a_lista_clientes(e):
        carrito.clear()
        actualizar_tabla()
        txt_busca_prod.value = ""; resultados_busqueda.controls.clear()
        container_principal.content = layout_seleccion_cliente
        page.update()

    # --- DISEÑO SELECCIÓN CLIENTE ---
    txt_busca_cliente = ft.TextField(label="Buscar cliente por nombre o RIF...", on_change=lambda e: realizar_busqueda_cliente(e), expand=True, **estilo_campo)
    lista_clientes = ft.ListView(expand=True, spacing=10)

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
                            ft.ElevatedButton("CREAR", bgcolor="#00897b", color="white", on_click=lambda _, cli=c: iniciar_factura_con_cliente(cli)),
                        ]),
                        padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "black12"))
                    )
                )
        page.update()

    layout_seleccion_cliente = ft.Column([
        ft.Row([txt_busca_cliente, ft.ElevatedButton("NUEVO CLIENTE", bgcolor="#004d40", color="white", height=50, on_click=lambda _: iniciar_factura_con_cliente(None))]),
        lista_clientes
    ], expand=True)

    # --- DISEÑO FORMULARIO FACTURA ---
    layout_formulario = ft.Row([
        ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Text("DATOS DEL CLIENTE", weight="bold", color="#004d40"), ft.Container(expand=True), ft.TextButton("Cambiar Cliente", on_click=volver_a_lista_clientes)]),
                    ft.Row([txt_cliente_id, txt_cliente_nombre]),
                    ft.Row([txt_cliente_dir, txt_cliente_zona]),
                    ft.Row([txt_cliente_email]),
                ]),
                padding=15, bgcolor="white", border_radius=8
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("AÑADIR PRODUCTOS", weight="bold", color="#004d40"),
                    ft.Row([txt_busca_prod]), 
                    ft.Container(content=resultados_busqueda, expand=True)
                ]),
                padding=15, bgcolor="white", border_radius=8, expand=True
            ),
        ], expand=1, spacing=15),
        ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("RESUMEN DE VENTA", weight="bold", color="#004d40"),
                    ft.Divider(),
                    ft.Container(content=ft.Column([tabla_carrito], scroll=ft.ScrollMode.ALWAYS), expand=True),
                    ft.Divider(),
                    ft.Row([txt_total_pago], alignment=ft.MainAxisAlignment.END),
                    ft.ElevatedButton("GUARDAR Y GENERAR PDF", bgcolor="#004d40", color="white", height=50, width=500, on_click=lambda e: procesar_factura(e))
                ]),
                padding=20, bgcolor="white", border_radius=8, expand=True
            )
        ], expand=1)
    ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.STRETCH, spacing=25, expand=True)

    def procesar_factura(e):
        if not carrito or not txt_cliente_id.value:
            mostrar_mensaje("Error: Debe seleccionar un cliente y productos")
            return
        
        monto_total = sum(item['subtotal'] for item in carrito)
        email_destino = txt_cliente_email.value.strip()
        
        datos_cliente = {
            "cedula_rif": txt_cliente_id.value, 
            "nombre_razon": txt_cliente_nombre.value, 
            "direccion": txt_cliente_dir.value, 
            "zona": txt_cliente_zona.value,
            "email": email_destino
        }
        
        # 1. Guardar en Base de Datos
        res = guardar_factura_completa(user_id, datos_cliente, carrito, monto_total)
        
        if res["success"]:
            res['cliente'] = datos_cliente
            
            # 2. Generar PDF (internamente usa numero_factura)
            ruta_generada = generar_factura_pdf(res, carrito)
            
            # 3. Lógica Opcional de Correo
            if email_destino and "@" in email_destino:
                mostrar_mensaje("Enviando correo...", color="#00897b")
                
                # Sincronizado con pdf_service: carpeta "facturas_generadas" y prefijo "Nota_"
                ruta_pdf = os.path.join("facturas_generadas", f"Nota_{res['numero_factura']}.pdf")
                
                exito_envio = enviar_factura_email(email_destino, res['numero_factura'], ruta_pdf)
                
                if exito_envio:
                    mostrar_mensaje("Venta guardada y correo enviado", color="#2e7d32")
                else:
                    mostrar_mensaje("Venta guardada, pero el correo no pudo enviarse")
            else:
                mostrar_mensaje("Venta guardada exitosamente", color="#2e7d32")
                
            volver_a_lista_clientes(None)

    container_principal = ft.Container(content=layout_seleccion_cliente, expand=True)

    return ft.Column([
        ft.Text("GENERAR NOTA DE ENTREGA", size=28, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=2),
        container_principal
    ], spacing=20, expand=True)