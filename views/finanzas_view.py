import flet as ft
import sqlite3
import os

DB_PATH = os.path.join("database", "sistema_ventas.db")

def finanzas_view(page: ft.Page):
    user_id = getattr(page, "user_id", None)

    def obtener_metricas():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. INVERSIÓN: Stock actual (Costo base * unidades en estante)
        cursor.execute("SELECT SUM(precio_costo * cantidad_unidades) as total FROM productos WHERE usuario_id = ?", (user_id,))
        inversion = cursor.fetchone()['total'] or 0.0

        # 2. INGRESOS: Dinero bruto de facturas pagadas
        cursor.execute("SELECT SUM(monto_total) as total FROM facturas WHERE usuario_id = ? AND estado = 'Pagado'", (user_id,))
        ingresos = cursor.fetchone()['total'] or 0.0

        # --- LÓGICA DE CONVERSIÓN SEGÚN TUS SCRIPTS (Caja vs Unid.) ---
        cursor.execute("""
            SELECT 
                SUM(
                    (p.precio_costo_total - p.precio_costo) * (CASE WHEN fd.tipo = 'Caja' THEN fd.cantidad * p.unidades_por_caja ELSE fd.cantidad END)
                ) as gasto_op,
                SUM(
                    p.precio_costo_total * (CASE WHEN fd.tipo = 'Caja' THEN fd.cantidad * p.unidades_por_caja ELSE fd.cantidad END)
                ) as costo_total_mercancia_vendida
            FROM factura_detalles fd
            JOIN facturas f ON fd.factura_id = f.id
            JOIN productos p ON fd.producto_id = p.id
            WHERE f.usuario_id = ? AND f.estado = 'Pagado'
        """, (user_id,))
        
        datos_calculados = cursor.fetchone()
        gastos_op = datos_calculados['gasto_op'] or 0.0
        costo_total_vendido = datos_calculados['costo_total_mercancia_vendida'] or 0.0
        
        # 4. GANANCIA: Ingresos Brutos - (Costo Base + Gasto Op de lo vendido)
        ganancia_real = ingresos - costo_total_vendido

        conn.close()
        return inversion, gastos_op, ingresos, ganancia_real

    def crear_tarjeta(titulo, valor, info_extra, color_base):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo.upper(), size=12, weight="bold", color=color_base),
                ft.Text(f"$ {valor:,.2f}", size=24, weight="bold", color="black"),
                ft.Text(info_extra, size=11, color="grey"),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="white",
            padding=25,
            border_radius=12,
            expand=True,
            height=150,
            border=ft.border.only(left=ft.BorderSide(5, color_base)),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#15000000")
        )

    inv, gast, ing, gan = obtener_metricas()

    # Fila de tarjetas que se expande
    tarjetas_row = ft.Row(
        controls=[
            crear_tarjeta("Inversión", inv, "Stock en almacén", "#2196F3"),
            crear_tarjeta("Gastos Op.", gast, "Transporte (Caja/Unid)", "#F44336"),
            crear_tarjeta("Ingresos", ing, "Total cobrado bruto", "#FF9800"),
            crear_tarjeta("Ganancia", gan, "Utilidad neta real", "#4CAF50"),
        ],
        spacing=20,
        expand=True,
    )

    # Contenedor principal que cubre toda la ventana (manteniendo tu diseño)
    container_blanco = ft.Container(
        content=ft.Column([
            ft.Text("Dashboard Financiero", size=22, weight="bold", color="#004d40"),
            ft.Divider(height=30, color="transparent"),
            tarjetas_row,
            ft.Divider(height=40),
            ft.Column([
                ft.Text("Notas de precisión contable:", size=14, weight="bold", color="black"),
                ft.Text("• Los Gastos Op. ahora detectan si la venta fue por Caja para multiplicar el flete correctamente.", size=13, color="grey"),
                ft.Text("• La Ganancia se calcula restando el Costo Total (Producto + Logística) a los Ingresos.", size=13, color="grey"),
            ], spacing=8)
        ], scroll=ft.ScrollMode.AUTO),
        bgcolor="white",
        padding=40,
        border_radius=20,
        expand=True,
        border=ft.border.all(1, "#E0E0E0"),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color="#11000000")
    )

    return ft.Column([
        ft.Text("FINANZAS", size=28, weight="bold", color="#00332a"),
        ft.Divider(color="#00332a", height=1, thickness=1),
        ft.Container(
            content=container_blanco, 
            expand=True, 
            padding=ft.padding.only(top=10)
        )
    ], spacing=10, expand=True)