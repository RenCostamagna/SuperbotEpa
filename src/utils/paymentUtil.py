import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_payment_intentions_to_api(client_data: list = None, product_data: list = None, phone_number: str = None) -> str:

    url = os.getenv('URL_API_PAGOS')
    client_data_formate = client_data[0] if client_data and len(client_data) > 0 else {}
    print("client_data_formate", client_data_formate)
    
    # Mapeo de productos utilizando comprensión de listas
    productos = [
        {
            "code": str(product_info.get("externalId", "")),
            "description": str(product_info.get("artículo_descripcion", "") or product_info.get("name", "")),
            "name": str(product_info.get("artículo_descripcion", "") or product_info.get("name", "")),
            "sku": str(product_info.get("externalId", "")),
            "quantity": int(product_info.get("stock", "0")),
            "total_amount": int(float(product_info.get("con_iva", "0").replace(',', '.')) * int(product_info.get("stock", "0"))) if product_info.get("con_iva", "0").replace(',', '.').replace('.', '', 1).isdigit() else 0,
            "unit_price": int(float(product_info.get("con_iva", "0")))
        }
        for product_info in product_data
    ]
    
    # Calcular el total de todos los productos
    total_amount = sum(producto["total_amount"] for producto in productos)

    payload = {
        "Amount": total_amount,
        "DNI": client_data_formate.get("cuit", ""),
        "CallbackUrl": f"https://superbproyecto.com/epa/payment?phone_number={phone_number}",
        "items": productos
    }
    
    response = requests.post(url, json=payload)
    print("response", response.json())

    # Obtener la URL de la respuesta
    if response.status_code == 201:
        response_data = response.json()
        print(response_data.get("generatedUrl"))
        generated_url = response_data.get("generatedUrl", "")  # Extraer el campo generatedUrl
        # Concatenar la URL base con la URL generada
        base_url = os.getenv('URL_PARA_USUARIO')
        generated_url_final = base_url + generated_url
        print("generated_url_final", generated_url_final)
        return generated_url_final  # Retornar solo el generatedUrl
    else:
        return "error"  # Retornar un string vacío en caso de error


#client_data = [{ "id": 1, "razon_social": "Juan Perez", "cuit": "2024567890", "retiro": "1234567890"}]
#product_data = [{"externalId": 1, "artículo_descripcion": "Producto 1", "stock": "1", "rubro": "rubro1", "con_iva": "17500.0"}]
#phone_number = "1234567890"
#link = send_payment_intentions_to_api(client_data, product_data, phone_number)
