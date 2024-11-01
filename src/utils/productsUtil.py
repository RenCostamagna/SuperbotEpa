import requests  # Importa la biblioteca requests
import os
from dotenv import load_dotenv
load_dotenv()

def fetch_products_from_api() -> list:
    url = os.getenv('URL_API_PRODUCTS')  # Reemplaza con la URL de tu API
    response = requests.get(url)
    
    exclude_external_id = 152  # ID del producto a excluir
    if response.status_code == 200:
        products = response.json()  # Almacena los productos en una variable
        products = [product for product in products if product['externalId'] != exclude_external_id]  # Filtra el producto
        
        # Multiplica el precio de cada producto por 1.21 para incluir el IVA y redondea a 2 decimales
        for product in products:
            product['con_iva'] = str(round(float(product['con_iva']) * 1.21, 2))  # Convierte a float, multiplica, redondea y luego a string
        
        return products  # Devuelve los productos filtrados
    else:
        print("Error al obtener productos:", response.status_code)
        return []
