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
        return products  # Devuelve los productos filtrados
    else:
        print("Error al obtener productos:", response.status_code)
        return []
