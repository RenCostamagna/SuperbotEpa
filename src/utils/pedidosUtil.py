import requests
import os   
from dotenv import load_dotenv
import json
import ast
from config.orderToBerna import Order, Client, Product

load_dotenv()

def send_order_to_api(data: list = None, client_data: list = None, phone_number: str = None) -> list:
    url = os.getenv('URL_API_PEDIDOS')
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        print("client_data", client_data)
        print("data", data)
        print("phone_number", phone_number)
        # Obtener el diccionario del cliente desde la lista y validar campos requeridos
        client_data_formate = client_data[0] if client_data and len(client_data) > 0 else {}
        print("client_data_formate", client_data_formate)
        # Validar y obtener datos del cliente con valores predeterminados
        client = Client(
            externalId=0,
            razonSocial=client_data_formate.get("razonSocial", ""),
            cuit=client_data_formate.get("cuit", ""),
            telefonos=phone_number or ""
        )
        retiro = client_data_formate.get("retiro", "")
        # Crear lista de productos con validación de claves
        productos = []
        for product_info in data:
            product = Product(
                externalId=product_info.get("externalId", ""),
                name=product_info.get("artículo_descripcion", "") or product_info.get("name", ""),
                category=product_info.get("rubro", "") or product_info.get("category", ""),
                stock=str(product_info.get("stock", "0")),
                priceIVA=str(product_info.get("con_iva", "0"))
            )
            productos.append(product)
        
        # Crear instancia de Order con client y todos los productos
        order = Order(
            orderId=0,
            retiro=retiro,
            client=client,
            productoList=productos
        )

        print("client", client)
        print("productos", productos)
        print("order", order)
        
        data_dict = order.to_dict()
        print("Datos enviados al API:", json.dumps(data_dict, indent=2))  # Agregar este log
        
        response = requests.post(
            url=url,
            json=data_dict,
            headers=headers
        )
        
        print("Status Code:", response.status_code)  # Agregar este log
        print("Respuesta del API:", response.text)   # Agregar este log
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al procesar los datos: {str(e)}")
        print(f"Detalles completos del error: {e.__class__.__name__}")  # Agregar este log
        return []
