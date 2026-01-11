import flet as ft
from data.database import insertar_producto

def agregar_producto_view(page: ft.Page):
    # Campos de texto sin iconos
    txt_codigo = ft.TextField(label="Código de Barras")
    txt_nombre = ft.TextField(label="Nombre del Producto", expand=True)
    txt_marca = ft.TextField(label="Marca")
    txt_categoria = ft.TextField(label="Categoría")
    
    txt_costo = ft.TextField(label="Costo", value="0", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    txt_porcentaje = ft.TextField(label="% Ganancia", value="0", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    txt_venta = ft.TextField(label="Precio Venta", value="0", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    txt_cantidad = ft.TextField(label="Stock Inicial", value="0", width=150, keyboard_type=ft.KeyboardType.NUMBER)

    def guardar_click(e):
        # Obtener ID del usuario logueado
        user_id = getattr(page, "user_id", None)
        
        if not txt_nombre.value:
            txt_nombre.error_text = "El nombre es obligatorio"
            page.update()
            return

        # Preparar los datos según el orden de la tabla productos en database.py
        datos = (
            user_id,
            txt_codigo.value,
            txt_nombre.value,
            "Unidad", # valor por defecto para unidades
            float(txt_costo.value or 0),
            float(txt_porcentaje.value or 0),
            float(txt_venta.value or 0),
            int(txt_cantidad.value or 0),
            txt_marca.value,
            txt_categoria.value
        )

        if insertar_producto(datos):
            # Limpiar campos tras éxito
            txt_nombre.value = ""
            txt_codigo.value = ""
            txt_marca.value = ""
            txt_categoria.value = ""
            txt_costo.value = "0"
            txt_porcentaje.value = "0"
            txt_venta.value = "0"
            txt_cantidad.value = "0"
            
            # Notificación de éxito
            page.snack_bar = ft.SnackBar(ft.Text("Producto guardado correctamente"))
            page.snack_bar.open = True
            page.update()

    # Layout de la vista
    return ft.Column([
        ft.Text("Agregar Nuevo Producto", size=25, weight="bold", color="#004d40"),
        ft.Divider(),
        ft.Row([
            txt_codigo, 
            txt_nombre
        ]),
        ft.Row([
            txt_marca, 
            txt_categoria
        ]),
        ft.Row([
            txt_costo, 
            txt_porcentaje, 
            txt_venta, 
            txt_cantidad
        ]),
        ft.Row([
            ft.ElevatedButton(
                "Guardar Producto", 
                on_click=guardar_click,
                style=ft.ButtonStyle(
                    bgcolor="#004d40", 
                    color="white",
                    padding=20
                )
            )
        ], alignment=ft.MainAxisAlignment.END)
    ], spacing=20, scroll=ft.ScrollMode.AUTO)