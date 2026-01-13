import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
# Eliminamos datetime/timedelta de aquí porque ya vienen en el diccionario 'res'

def generar_factura_pdf(res, carrito):
    # --- CONFIGURACIÓN DE CARPETA DE DESTINO ---
    carpeta_destino = "facturas_generadas"
    
    # Crear la carpeta si no existe
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
    
    # IMPORTANTE: Cambiamos res['numero'] por res['numero_factura']
    nombre_archivo = f"Nota_{res['numero_factura']}.pdf"
    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
    
    # Crear el canvas
    c = canvas.Canvas(ruta_completa, pagesize=letter)
    width, height = letter

    # --- ENCABEZADO IZQUIERDO ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "Inversiones y suministro")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, height - 75, "Zamora 77")

    # --- ENCABEZADO DERECHO (INFO NOTA) ---
    c.setFont("Helvetica", 16)
    c.drawRightString(width - 40, height - 50, "Nota de entrega")
    
    # Usamos numero_factura para el ID visual
    try:
        # Intentamos extraer solo los números de "FAC-2024..." para el formato 000001
        solo_numeros = res['numero_factura'].split('-')[-1]
        num_entero = int(solo_numeros[-6:]) # Tomamos los últimos 6 dígitos
        c.setFont("Helvetica", 16)
        c.drawRightString(width - 40, height - 75, f"{num_entero:06d}")
    except:
        c.drawRightString(width - 40, height - 75, str(res['numero_factura']))

    # --- FECHAS (Desde la Base de Datos) ---
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(500, height - 105, "Emisión:")
    c.setFont("Helvetica", 10)
    # Usamos la fecha que calculó la DB
    c.drawRightString(width - 40, height - 105, res['fecha_emision'])
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(500, height - 120, "Vence:")
    c.setFont("Helvetica", 10)
    # Usamos la fecha de vencimiento que calculó la DB
    c.drawRightString(width - 40, height - 120, res['fecha_vencimiento'])

    # --- DATOS DEL CLIENTE ---
    y_cli = height - 125
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_cli, "Nombre o razón social:")
    c.setFont("Helvetica", 10)
    c.drawString(155, y_cli, f"{res['cliente']['nombre_razon']}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_cli - 15, "Cédula/rif:")
    c.setFont("Helvetica", 10)
    c.drawString(100, y_cli - 15, f"{res['cliente']['cedula_rif']}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_cli - 30, "Dirección:")
    c.setFont("Helvetica", 10)
    c.drawString(95, y_cli - 30, f"{res['cliente']['direccion']}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_cli - 45, "Zona:")
    c.setFont("Helvetica", 10)
    c.drawString(75, y_cli - 45, f"{res['cliente']['zona']}")
    
    # Opcional: Mostrar correo en el PDF si existe
    if res['cliente'].get('email'):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y_cli - 60, "Correo:")
        c.setFont("Helvetica", 10)
        c.drawString(85, y_cli - 60, f"{res['cliente']['email']}")

    # --- TABLA DE PRODUCTOS ---
    y_table = y_cli - 85
    c.setFont("Helvetica-Bold", 11)
    c.drawString(45, y_table, "Producto")
    c.drawCentredString(320, y_table, "Cantidad")
    c.drawCentredString(390, y_table, "Unidad")
    c.drawCentredString(470, y_table, "Precio und")
    c.drawCentredString(540, y_table, "Precio total")
    
    c.setStrokeColorRGB(0.2, 0.2, 0.7)
    c.setLineWidth(1.5)
    c.line(40, y_table - 10, width - 40, y_table - 10)
    
    y = y_table - 30
    c.setFont("Helvetica", 10)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    
    for item in carrito:
        c.drawString(45, y, item['nombre'].upper())
        c.drawCentredString(320, y, str(item['cantidad']))
        c.drawCentredString(390, y, "UNID")
        c.drawCentredString(470, y, f"{item['precio']:.2f}$")
        c.drawCentredString(540, y, f"{item['subtotal']:.2f}$")
        y -= 20
        if y < 110: 
            c.showPage()
            y = height - 50

    # --- TOTALES ---
    c.setStrokeColorRGB(0.2, 0.2, 0.7)
    c.setLineWidth(1.5)
    c.line(40, 100, width - 40, 100)
    
    c.setFont("Helvetica-Bold", 12)
    monto_total = sum(item['subtotal'] for item in carrito)
    c.drawRightString(500, 80, "Monto total a pagar:")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 50, 80, f"{monto_total:,.2f}$")

    c.save()
    print(f"PDF guardado en: {ruta_completa}")
    
    return ruta_completa # Retornamos la ruta para que el mailer sepa dónde buscar el archivo