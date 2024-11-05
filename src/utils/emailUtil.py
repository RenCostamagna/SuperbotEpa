import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
import os
load_dotenv()

def send_email(status: str, client_data: list, product_list: list) -> str:   
    # Datos del remitente
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')

    # Datos del destinatario
    receiver_email = os.getenv('EMAIL_RECEIVER')

    # Configurar el mensaje
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = 'Nuevo pedido registrado'  # Asunto del correo

    # Formatear datos del cliente
    client_details = "\nDatos del Cliente:\n"
    if client_data and isinstance(client_data, list) and len(client_data) > 0:
        client_dict = client_data[0]  # Tomamos el primer diccionario de la lista
        # Accedemos a campos específicos del diccionario
        client_details += f"Razon social: {client_dict.get('razonSocial', 'No disponible')}\n"
        client_details += f"Cuit o DNI: {client_dict.get('cuit', 'No disponible')}\n"
    else:
        client_details += "No hay datos del cliente disponibles\n"

    # Formatear lista de productos
    products_details = "\nProductos:\n"
    total_amount = 0  # Inicializar el total
    for product in product_list:
        stock = int(product.get('stock', '0'))
        price_with_tax = float(product.get('con_iva', '0'))
        total_amount += stock * price_with_tax  # Sumar al total
        products_details += f"- {product.get('artículo_descripcion')}: {stock} unidades - ${price_with_tax} - Total: ${stock * price_with_tax}\n"

    products_details += f"\nTotal general: ${total_amount}\n"  # Agregar total general

    formated_shipp = f"DETALLES DEL PEDIDO:{client_details}{products_details}"
    
    # Cuerpo del correo (puedes tener texto plano y/o HTML)
    body = f'Procesalo lo antes posible.\n\n{formated_shipp}\n\nSaludos!\n\n{status}'
    msg.attach(MIMEText(body, 'plain'))

    # Conectar al servidor SMTP de Gmail
    try:
        # Establece una conexión con el servidor SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Iniciar conexión segura
        server.login(sender_email, sender_password)  # Autenticación

        # Envía el correo
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)

        # Cierra la conexión al servidor SMTP
        server.quit()

        print("Correo enviado exitosamente")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
