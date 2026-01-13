import flet as ft
import sqlite3
import os
from datetime import datetime
from services.pdf_service import generar_factura_pdf 

DB_PATH = os.path.join("database", "sistema_ventas.db")

def historial_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    
    # --- VARIABLES DE ESTADO (Estilo Inventario) ---
    state = {
        "pagina": 1, 
        "por_pagina": 8,
        "filtro_estado": "En Proceso"
    }

    # --- ESTILO CAMPOS ---
    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="black", weight="bold"),
        "border_color": "#004d40",
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
        "bgcolor": "#FFFFFF"
    }

    # --- ELEMENTOS UI ---
    txt_buscar = ft.TextField(
        label="Buscar por cliente, RIF o número de factura...",
        expand=True,
        on_change=lambda e: ejecutar_filtro(),
        **estilo_campo
    )
    lista_facturas = ft.ListView(expand=True, spacing=10)
    
    # Elementos del Detalle (ORIGINALES)
    lbl_detalle_titulo = ft.Text("", size=22, weight="bold", color="#004d40")
    lbl_fecha_emision = ft.Text("", size=14, color="black")
    lbl_fecha_vence = ft.Text("", size=14, color="black")
    lbl_cliente_nombre = ft.Text("", size=16, color="black") 
    lbl_cliente_rif = ft.Text("", size=14, color="black")
    lbl_cliente_dir = ft.Text("", size=14, color="black")
    lbl_cliente_zona = ft.Text("", size=14, color="black")
    lbl_monto_total_final = ft.Text("", size=22, weight="bold", color="#004d40")

    tabla_detalle = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Producto", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Cant.", color="black", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Empaque", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Precio Ref.", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Subtotal", color="black", weight="bold")),
        ],
        rows=[]
    )

    # --- FUNCIONES DE NAVEGACIÓN Y CARGA ---
    def ejecutar_filtro(estado=None):
        if estado: state["filtro_estado"] = estado
        state["pagina"] = 1
        cargar_datos()

    def nav_ant(e):
        if state["pagina"] > 1:
            state["pagina"] -= 1
            cargar_datos()

    def nav_sig(e):
        state["pagina"] += 1
        cargar_datos()

    def cargar_datos():
        # Actualizar botones de filtro
        for btn, label in [(btn_tab_proceso, "En Proceso"), (btn_tab_pagado, "Pagado"), (btn_tab_vencido, "Vencido")]:
            btn.bgcolor = "#004d40" if state["filtro_estado"] == label else "#EEEEEE"
            btn.color = "white" if state["filtro_estado"] == label else "black"

        lista_facturas.controls.clear()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        busqueda = f"%{txt_buscar.value}%" if txt_buscar.value else "%"
        offset = (state["pagina"] - 1) * state["por_pagina"]

        cursor.execute("""
            SELECT COUNT(*) FROM facturas f JOIN clientes c ON f.cliente_id = c.id
            WHERE f.usuario_id = ? AND f.estado = ?
            AND (c.nombre_razon LIKE ? OR f.numero_factura LIKE ? OR c.cedula_rif LIKE ?)
        """, (user_id, state["filtro_estado"], busqueda, busqueda, busqueda))
        total_items = cursor.fetchone()[0]
        total_paginas = (total_items + state["por_pagina"] - 1) // state["por_pagina"]

        query = """
            SELECT f.*, c.nombre_razon, c.cedula_rif 
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.usuario_id = ? AND f.estado = ?
            AND (c.nombre_razon LIKE ? OR f.numero_factura LIKE ? OR c.cedula_rif LIKE ?)
            ORDER BY f.id DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, (user_id, state["filtro_estado"], busqueda, busqueda, busqueda, state["por_pagina"], offset))
        
        for f in cursor.fetchall():
            lista_facturas.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f"NOTA: {f['numero_factura']}", weight="bold", size=14, color="#004d40"),
                            ft.Text(f"Cliente: {f['nombre_razon']} {f['cedula_rif']}", size=14, color="black"),
                        ], expand=True, spacing=2),
                        ft.Column([
                            ft.Text(f"{f['monto_total']:.2f}$", size=16, color="#004d40", weight="bold"),
                            ft.Text(f"Vence: {f['fecha_vencimiento']}", size=11, color="grey"),
                        ], horizontal_alignment="end", spacing=2),
                        ft.Row([
                            ft.ElevatedButton("PAGAR", bgcolor="#004d40", color="white", height=30, 
                                              on_click=lambda _, fid=f['id']: procesar_pago(fid)) if f['estado'] != "Pagado" else ft.Container(),
                            ft.ElevatedButton("VER", bgcolor="#26a69a", color="white", height=30,
                                              on_click=lambda _, fact=f: mostrar_detalle_factura(fact)),
                        ], spacing=10)
                    ]),
                    padding=12, bgcolor="#FFFFFF", border_radius=8, border=ft.border.all(1, "black12")
                )
            )

        txt_info_paginacion.value = f"Página {state['pagina']} de {max(1, total_paginas)} (Total: {total_items})"
        btn_prev.disabled = state["pagina"] == 1
        btn_next.disabled = state["pagina"] >= total_paginas
        
        conn.close()
        page.update()

    def mostrar_detalle_factura(factura):
        tabla_detalle.rows.clear()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (factura['cliente_id'],))
        cliente = cursor.fetchone()
        
        lbl_detalle_titulo.value = f"NOTA: {factura['numero_factura']}"
        lbl_fecha_emision.value = f"Emisión: {factura['fecha_emision']}"
        lbl_fecha_vence.value = f"Vence: {factura['fecha_vencimiento']}"
        lbl_cliente_nombre.value = cliente['nombre_razon'] if cliente else "N/A"
        lbl_cliente_rif.value = cliente['cedula_rif'] if cliente else "N/A"
        lbl_cliente_dir.value = cliente['direccion'] if cliente else "N/A"
        lbl_cliente_zona.value = cliente['zona'] if cliente else "N/A"
        
        cursor.execute("""
            SELECT fd.cantidad, fd.precio_unitario, fd.tipo, p.nombre_producto 
            FROM factura_detalles fd
            JOIN productos p ON fd.producto_id = p.id
            WHERE fd.factura_id = ?
        """, (factura['id'],))
        
        detalles = cursor.fetchall()
        for p in detalles:
            tipo_empaque = str(p['tipo']).upper() if p['tipo'] else "UNID."
            tabla_detalle.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p['nombre_producto'].upper(), color="black")),
                ft.DataCell(ft.Text(str(p['cantidad']), color="black")),
                ft.DataCell(ft.Text(tipo_empaque, color="black")),
                ft.DataCell(ft.Text(f"{p['precio_unitario']:.2f}$", color="black")),
                ft.DataCell(ft.Text(f"{(p['cantidad'] * p['precio_unitario']):.2f}$", color="black")),
            ]))
        
        lbl_monto_total_final.value = f"Monto Total: {factura['monto_total']:.2f}$"
        btn_pagar_en_detalle.visible = (factura['estado'] != "Pagado")
        btn_pagar_en_detalle.on_click = lambda _: procesar_pago(factura['id'])
        btn_pdf_detalle.on_click = lambda _: regenerar_pdf(factura, detalles)
        
        conn.close()
        container_historial.content = layout_detalle 
        page.update()

    def volver_al_listado(e):
        container_historial.content = layout_listado
        cargar_datos() 
        page.update()

    def procesar_pago(factura_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE facturas SET estado = 'Pagado' WHERE id = ?", (factura_id,))
        conn.commit()
        conn.close()
        volver_al_listado(None)

    def regenerar_pdf(factura_data, detalles_db):
        carrito_formateado = []
        for d in detalles_db:
            carrito_formateado.append({
                "nombre": d["nombre_producto"], "cantidad": d["cantidad"],
                "tipo": d["tipo"], "precio_unitario": d["precio_unitario"],
                "subtotal": d["cantidad"] * d["precio_unitario"]
            })
        res_pdf = {
            "numero_factura": factura_data["numero_factura"],
            "fecha_emision": factura_data["fecha_emision"],
            "fecha_vencimiento": factura_data["fecha_vencimiento"],
            "cliente": {
                "nombre_razon": lbl_cliente_nombre.value, "cedula_rif": lbl_cliente_rif.value,
                "direccion": lbl_cliente_dir.value, "zona": lbl_cliente_zona.value
            }
        }
        generar_factura_pdf(res_pdf, carrito_formateado)

    # --- BOTONES ---
    btn_tab_proceso = ft.ElevatedButton("EN PROCESO", on_click=lambda _: ejecutar_filtro("En Proceso"))
    btn_tab_pagado = ft.ElevatedButton("PAGADAS", on_click=lambda _: ejecutar_filtro("Pagado"))
    btn_tab_vencido = ft.ElevatedButton("VENCIDAS", on_click=lambda _: ejecutar_filtro("Vencido"))
    
    btn_prev = ft.ElevatedButton("ANTERIOR", on_click=nav_ant, bgcolor="#004d40", color="white")
    btn_next = ft.ElevatedButton("SIGUIENTE", on_click=nav_sig, bgcolor="#004d40", color="white")
    txt_info_paginacion = ft.Text(color="black", weight="bold")

    btn_pagar_en_detalle = ft.ElevatedButton("COBRAR NOTA", bgcolor="#004d40", color="white", height=45)
    btn_pdf_detalle = ft.ElevatedButton("REGENERAR PDF", bgcolor="#c62828", color="white", height=45)

    # --- LAYOUTS ---
    layout_listado = ft.Column([
        ft.Row([btn_tab_proceso, btn_tab_pagado, btn_tab_vencido], spacing=10),
        ft.Row([txt_buscar, ft.ElevatedButton("FILTRAR", bgcolor="#004d40", color="white", height=50, on_click=lambda _: ejecutar_filtro())], spacing=10),
        ft.Container(content=lista_facturas, expand=True),
        ft.Row([btn_prev, ft.Container(txt_info_paginacion, padding=10), btn_next], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    ], expand=True)

    layout_detalle = ft.Column([
        ft.Row([
            ft.ElevatedButton("VOLVER AL LISTADO", bgcolor="#455a64", color="white", height=45, on_click=volver_al_listado),
            ft.Container(expand=True),
            ft.Row([btn_pdf_detalle, btn_pagar_en_detalle], spacing=10)
        ]),
        ft.Container(
            padding=25, bgcolor="white", border_radius=10, border=ft.border.all(1, "black12"),
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Inversiones y suministro", size=16, weight="bold", color="black"),
                        ft.Text("Zamora 77", size=20, weight="bold", color="#004d40"),
                    ]),
                    ft.Container(expand=True),
                    ft.Column([
                        lbl_detalle_titulo, lbl_fecha_emision, lbl_fecha_vence,
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ]),
                ft.Divider(height=30),
                ft.Column([
                    ft.Row([ft.Text("Nombre o razón social: ", weight="bold", color="black"), lbl_cliente_nombre]),
                    ft.Row([ft.Text("Cédula/rif: ", weight="bold", color="black"), lbl_cliente_rif]),
                    ft.Row([ft.Text("Dirección: ", weight="bold", color="black"), lbl_cliente_dir]),
                    ft.Row([ft.Text("Zona: ", weight="bold", color="black"), lbl_cliente_zona]),
                ], spacing=5),
                ft.Divider(height=30),
                ft.Row([tabla_detalle], scroll=ft.ScrollMode.AUTO),
                ft.Divider(height=30, color="transparent"),
                ft.Row([lbl_monto_total_final], alignment=ft.MainAxisAlignment.END),
            ], scroll=ft.ScrollMode.AUTO, expand=True)
        )
    ], expand=True)

    container_historial = ft.Container(content=layout_listado, expand=True)
    cargar_datos()

    return ft.Column([
        ft.Text("HISTORIAL Y COBRANZAS", size=28, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=1, thickness=1),
        container_historial
    ], spacing=20, expand=True)