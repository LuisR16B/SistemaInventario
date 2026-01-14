import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit # Importante para dividir el texto

def generar_factura_pdf(res, carrito):
    carpeta_destino = "facturas_generadas"
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
    
    try:
        if isinstance(res['numero_factura'], str) and "-" in res['numero_factura']:
            num_solo = res['numero_factura'].split('-')[-1]
            num_final = f"{int(num_solo):08d}"
        else:
            num_final = f"{int(res['numero_factura']):08d}"
    except:
        num_final = str(res['numero_factura'])

    nombre_archivo = f"Nota_{num_final}.pdf"
    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
    
    c = canvas.Canvas(ruta_completa, pagesize=letter)
    width, height = letter
    COLOR_APP = (0/255, 77/255, 64/255)

    # --- ENCABEZADO --- (Sin cambios)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "Inversiones y suministro")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 75, "Zamora 77")
    c.setFont("Helvetica", 16)
    c.drawRightString(width - 40, height - 50, "Nota de entrega")
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(width - 40, height - 75, num_final)

    # --- FECHAS ---
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(500, height - 105, "Emisión:")
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 40, height - 105, res.get('fecha_emision', 'N/A'))
    c.drawRightString(500, height - 120, "Vence:")
    c.drawRightString(width - 40, height - 120, res.get('fecha_vencimiento', 'N/A'))

    # --- DATOS DEL CLIENTE ---
    y_cli = height - 140
    def draw_client_data(label, value, y_pos):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y_pos, label)
        c.setFont("Helvetica", 10)
        c.drawString(45 + c.stringWidth(label, "Helvetica-Bold", 10), y_pos, str(value))

    draw_client_data("Nombre o razón social: ", res['cliente']['nombre_razon'], y_cli)
    draw_client_data("Cédula/rif: ", res['cliente']['cedula_rif'], y_cli - 15)
    draw_client_data("Dirección: ", res['cliente']['direccion'], y_cli - 30)
    draw_client_data("Zona: ", res['cliente']['zona'], y_cli - 45)

    # --- TABLA DE PRODUCTOS ---
    y_table = y_cli - 85
    c.setFont("Helvetica-Bold", 11)
    c.drawString(45, y_table, "Producto")
    c.drawCentredString(300, y_table, "Cant.")
    c.drawCentredString(365, y_table, "Empaque")
    c.drawCentredString(460, y_table, "Precio Ref.")
    c.drawCentredString(540, y_table, "Subtotal")
    
    c.setStrokeColorRGB(*COLOR_APP)
    c.setLineWidth(1.5)
    c.line(40, y_table - 10, width - 40, y_table - 10)
    
    y = y_table - 30
    c.setFont("Helvetica", 10)
    
    # Ancho máximo para la columna de producto (aprox hasta llegar a 'Cant.')
    ancho_max_nombre = 220 

    for item in carrito:
        # 1. Dividir el nombre en líneas que quepan en el ancho
        nombre_prod = str(item['nombre']).upper()
        lineas_nombre = simpleSplit(nombre_prod, "Helvetica", 10, ancho_max_nombre)
        
        # Guardamos la 'y' inicial para las otras columnas
        y_inicio_fila = y 

        # 2. Dibujar cada línea del nombre
        for linea in lineas_nombre:
            c.drawString(45, y, linea)
            y -= 12 # Espaciado entre líneas del nombre

        # 3. Dibujar el resto de columnas (alineadas con la primera línea del nombre)
        y_resto = y_inicio_fila
        c.drawCentredString(300, y_resto, str(item['cantidad']))
        tipo_empaque = str(item.get('tipo', 'UNID')).upper()
        c.drawCentredString(365, y_resto, tipo_empaque)
        
        precio_val = item.get('precio_unitario', 0)
        c.drawCentredString(460, y_resto, f"{precio_val:,.2f}$")
        c.drawCentredString(540, y_resto, f"{item['subtotal']:,.2f}$")
        
        # 4. Preparar la 'y' para el siguiente producto
        # Si el nombre ocupó varias líneas, dejamos un espacio extra
        y = min(y, y_resto - 15) - 5 

        # Salto de página si se acaba el espacio
        if y < 110: 
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

    # --- TOTALES ---
    c.setStrokeColorRGB(*COLOR_APP)
    c.setLineWidth(1.5)
    c.line(40, 100, width - 40, 100)
    
    c.setFont("Helvetica-Bold", 12)
    monto_total = sum(item['subtotal'] for item in carrito)
    c.drawRightString(500, 80, "Monto total a pagar:")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 50, 80, f"{monto_total:,.2f}$")

    c.save()
    return ruta_completa