import flet as ft
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("database", "sistema_ventas.db")

def historial_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)
    
    # Manejo de estado del filtro
    class EstadoFiltro:
        def __init__(self):
            self.actual = "En Proceso"
    
    filtro = EstadoFiltro()

    # --- ESTILOS ---
    estilo_campo = {
        "color": "black",
        "label_style": ft.TextStyle(color="#004d40", weight="bold"),
        "border_color": "#004d40",
        "focused_border_color": "#00897b",
        "border": ft.InputBorder.OUTLINE,
        "bgcolor": "#FFFFFF"
    }

    # --- ELEMENTOS UI ---
    txt_buscar = ft.TextField(
        label="Buscar por cliente, RIF o número de factura...",
        expand=True,
        on_change=lambda e: cargar_facturas(),
        **estilo_campo
    )
    lista_facturas = ft.ListView(expand=True, spacing=10)

    # Elementos del Detalle
    lbl_detalle_titulo = ft.Text("", size=22, weight="bold", color="#004d40")
    lbl_fecha_emision = ft.Text("", size=14, color="black")
    lbl_fecha_vence = ft.Text("", size=14, color="black")
    lbl_cliente_nombre = ft.Text("", size=14, weight="bold", color="black")
    lbl_cliente_rif = ft.Text("", size=14, color="black")
    lbl_cliente_dir = ft.Text("", size=14, color="black")
    lbl_cliente_zona = ft.Text("", size=14, color="black")
    lbl_monto_total_final = ft.Text("", size=22, weight="bold", color="#004d40")

    tabla_detalle = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Producto", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Cant.", color="black", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Unidad", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Precio Und", color="black", weight="bold")),
            ft.DataColumn(ft.Text("Total", color="black", weight="bold")),
        ],
        rows=[]
    )

    # --- LÓGICA DE COBRO ---
    def procesar_pago(factura_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE facturas SET estado = 'Pagado' WHERE id = ?", (factura_id,))
        conn.commit()
        conn.close()
        # Regresar al listado si estábamos en detalle y refrescar
        container_historial.content = layout_listado
        cargar_facturas()
        page.update()

    # --- NAVEGACIÓN Y VISTAS ---
    def mostrar_detalle_factura(factura):
        tabla_detalle.rows.clear()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (factura['cliente_id'],))
        cliente = cursor.fetchone()
        
        lbl_detalle_titulo.value = f"NOTA DE ENTREGA: {factura['numero_factura']}"
        lbl_fecha_emision.value = f"Emisión: {factura['fecha_emision']}"
        lbl_fecha_vence.value = f"Vence: {factura['fecha_vencimiento']}"
        lbl_cliente_nombre.value = cliente['nombre_razon'].upper() if cliente else "N/A"
        lbl_cliente_rif.value = cliente['cedula_rif'] if cliente else "N/A"
        lbl_cliente_dir.value = cliente['direccion'] if cliente else "N/A"
        lbl_cliente_zona.value = cliente['zona'] if cliente else "N/A"
        
        cursor.execute("""
            SELECT fd.*, p.nombre_producto 
            FROM factura_detalles fd
            JOIN productos p ON fd.producto_id = p.id
            WHERE fd.factura_id = ?
        """, (factura['id'],))
        
        for p in cursor.fetchall():
            tabla_detalle.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p['nombre_producto'].upper(), color="black")),
                ft.DataCell(ft.Text(str(p['cantidad']), color="black")),
                ft.DataCell(ft.Text("UNIDADES", color="black")),
                ft.DataCell(ft.Text(f"{p['precio_unitario']:.2f}$", color="black")),
                ft.DataCell(ft.Text(f"{p['cantidad'] * p['precio_unitario']:.2f}$", color="black")),
            ]))
        conn.close()
        
        lbl_monto_total_final.value = f"Monto total a pagar: {factura['monto_total']:.2f}$"
        
        # Botón de pagar en el detalle (Solo si no está pagada)
        btn_pagar_en_detalle.visible = True if factura['estado'] != "Pagado" else False
        btn_pagar_en_detalle.on_click = lambda _: procesar_pago(factura['id'])
        
        container_historial.content = layout_detalle
        page.update()

    def volver_al_listado(e):
        container_historial.content = layout_listado
        page.update()

    # --- CARGA DE DATOS ---
    def cargar_facturas(estado=None):
        if estado: filtro.actual = estado
        
        # Estilo de botones superiores
        for btn, label in [(btn_tab_proceso, "En Proceso"), (btn_tab_pagado, "Pagado"), (btn_tab_vencido, "Vencido")]:
            btn.bgcolor = "#004d40" if filtro.actual == label else "#EEEEEE"
            btn.color = "white" if filtro.actual == label else "black"

        lista_facturas.controls.clear()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Sincronizar estados de vencimiento
        hoy = datetime.now()
        cursor.execute("SELECT id, fecha_vencimiento FROM facturas WHERE estado = 'En Proceso' AND usuario_id = ?", (user_id,))
        for f in cursor.fetchall():
            try:
                if hoy > datetime.strptime(f['fecha_vencimiento'], "%d-%m-%Y"):
                    cursor.execute("UPDATE facturas SET estado = 'Vencido' WHERE id = ?", (f['id'],))
            except: continue
        conn.commit()

        query = """
            SELECT f.*, c.nombre_razon, c.cedula_rif 
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.usuario_id = ? AND f.estado = ?
            AND (c.nombre_razon LIKE ? OR f.numero_factura LIKE ? OR c.cedula_rif LIKE ?)
            ORDER BY f.id DESC
        """
        busqueda = f"%{txt_buscar.value}%"
        cursor.execute(query, (user_id, filtro.actual, busqueda, busqueda, busqueda))
        
        for f in cursor.fetchall():
            border_col = "#FF9800" if f['estado'] == "En Proceso" else "#4CAF50" if f['estado'] == "Pagado" else "#F44336"
            
            # Botón de Pago Rápido en la Lista
            btn_pago_lista = ft.ElevatedButton(
                "PAGAR", 
                bgcolor="#2E7D32", 
                color="white",
                on_click=lambda _, fid=f['id']: procesar_pago(fid)
            ) if f['estado'] != "Pagado" else ft.Container()

            lista_facturas.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=5, bgcolor=border_col, border_radius=5),
                        ft.Column([
                            ft.Text(f"FACTURA: {f['numero_factura']}", weight="bold", size=14, color="#004d40"),
                            ft.Text(f"{f['nombre_razon']}", size=14, color="black"),
                        ], expand=True, spacing=2),
                        ft.Column([
                            ft.Text(f"{f['monto_total']:.2f}$", size=16, color="#004d40", weight="bold"),
                            ft.Text(f"Vence: {f['fecha_vencimiento']}", size=11, color="grey"),
                        ], horizontal_alignment="end", spacing=2),
                        ft.Row([
                            btn_pago_lista,
                            ft.ElevatedButton("VER", bgcolor="#00897b", color="white", 
                                             on_click=lambda _, fact=f: mostrar_detalle_factura(fact)),
                        ], spacing=8)
                    ]),
                    padding=12, bgcolor="#FFFFFF", border_radius=8, border=ft.border.all(1, "black12")
                )
            )
        conn.close()
        page.update()

    # --- COMPONENTES NAVEGACIÓN ---
    btn_tab_proceso = ft.ElevatedButton(content=ft.Text("EN PROCESO"), on_click=lambda _: cargar_facturas("En Proceso"))
    btn_tab_pagado = ft.ElevatedButton(content=ft.Text("PAGADAS"), on_click=lambda _: cargar_facturas("Pagado"))
    btn_tab_vencido = ft.ElevatedButton(content=ft.Text("VENCIDAS"), on_click=lambda _: cargar_facturas("Vencido"))
    
    btn_pagar_en_detalle = ft.ElevatedButton("MARCAR COMO PAGADA", bgcolor="#004d40", color="white", height=45)

    # --- LAYOUTS ---
    layout_listado = ft.Column([
        ft.Row([btn_tab_proceso, btn_tab_pagado, btn_tab_vencido], spacing=10),
        ft.Row([txt_buscar, ft.ElevatedButton("BUSCAR", bgcolor="#004d40", color="white", height=50, on_click=lambda _: cargar_facturas())]),
        lista_facturas
    ], expand=True)

    layout_detalle = ft.Column([
        ft.Row([
            ft.ElevatedButton("← VOLVER AL LISTADO", bgcolor="#00897b", color="white", on_click=volver_al_listado),
            ft.Container(expand=True),
            btn_pagar_en_detalle
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
                        lbl_detalle_titulo,
                        lbl_fecha_emision,
                        lbl_fecha_vence,
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ]),
                ft.Divider(height=30),
                ft.Column([
                    ft.Row([ft.Text("Nombre o razón social: ", weight="bold", color="black"), lbl_cliente_nombre]),
                    ft.Row([ft.Text("Cédula/RIF: ", weight="bold", color="black"), lbl_cliente_rif]),
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
    cargar_facturas("En Proceso")

    return ft.Column([
        ft.Text("HISTORIAL Y COBRANZAS", size=28, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=2),
        container_historial
    ], spacing=20, expand=True)