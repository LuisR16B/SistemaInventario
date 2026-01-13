import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def enviar_factura_email(destinatario, numero_nota, ruta_pdf):
    """
    Servicio para enviar Notas de Entrega en formato PDF por correo electrónico.
    """
    # --- CONFIGURACIÓN DE CREDENCIALES ---
    # RECUERDA: Usa una 'Contraseña de Aplicación' si usas Gmail
    remitente = "lerojasbonilla.123@gmail.com"
    password = "wmub oilf mubl mgln" 

    # Validación básica del correo
    if not destinatario or "@" not in destinatario:
        print(f"Error: El correo '{destinatario}' no es válido.")
        return False

    # Verificar que el archivo PDF existe antes de intentar enviarlo
    if not os.path.exists(ruta_pdf):
        print(f"Error: No se encontró el archivo en {ruta_pdf}")
        return False

    # Estructura del mensaje
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = f"Nota de Entrega {numero_nota} - Zamora 77"

    cuerpo = f"""
    Hola,
    
    Adjunto enviamos la Nota de Entrega {numero_nota} correspondiente a su compra.
    
    Inversiones y Suministro Zamora 77 le agradece su confianza.
    """
    msg.attach(MIMEText(cuerpo, 'plain'))

    # Proceso de adjuntar el PDF
    try:
        with open(ruta_pdf, "rb") as adjunto:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(adjunto.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition', 
                f"attachment; filename={os.path.basename(ruta_pdf)}"
            )
            msg.attach(part)

        # Conexión Segura con el servidor SMTP (Gmail)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Encriptación de la conexión
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        
        print(f"Correo enviado exitosamente a: {destinatario}")
        return True

    except Exception as e:
        print(f"Fallo en el servicio de correo: {e}")
        return False