import requests  # Importa la biblioteca requests
import os
from dotenv import load_dotenv
load_dotenv()

def fetch_clients_from_api() -> list:
    url = os.getenv('URL_API_CLIENTS')  # Reemplaza con la URL de tu API
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()  # Devuelve los productos en formato JSON
    else:
        print("Error al obtener productos:", response.status_code)
        return []