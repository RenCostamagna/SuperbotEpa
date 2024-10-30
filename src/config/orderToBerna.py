from typing import List

class Client:
    def __init__(self, externalId: str, razonSocial: str, cuit: str, 
                 direccion: str = None, telefonos: str = None, 
                 email: str = None, zona: str = None):
        self.externalId = "6"
        self.razonSocial = razonSocial
        self.cuit = cuit
        self.direccion = ""
        self.telefonos = telefonos
        self.email = ""
        self.zona = ""

    def to_dict(self):
        return self.__dict__

class Product:
    def __init__(self, externalId: str, name: str = None, category: str = None, 
                 stock: str = None, priceIVA: str = None, 
                 artículo_descripcion: str = None, rubro: str = None):
        self.id = 0
        # Convertir externalId a entero
        self.externalId = int(externalId) if externalId is not None else 0
        # Usar articulo_descripcion si está disponible, sino usar name
        self.name = artículo_descripcion or name or ""
        # Usar rubro si está disponible, sino usar category
        self.category = rubro or category or ""
        # Convertir stock a entero
        self.stock = str(stock) if stock is not None else "0"
        self.moneda = None
        self.priceIVA = str(priceIVA) if priceIVA is not None else "0"
        self.priceSinIVA = None
        self.isNew = True
        self.mustSend = True

    def to_dict(self):
        return self.__dict__

class Order:
    def __init__(self, orderId: int, retiro: str, client: Client, productoList: List[Product]):
        self.orderId = orderId
        self.retiro = retiro
        self.client = client
        self.productoList = productoList

    def to_dict(self):
        return {
            "orderId": self.orderId,
            "retiro": self.retiro,
            "client": self.client.to_dict(),
            "productoList": [p.to_dict() for p in self.productoList]
        }


__all__ = ["Client", "Product", "Order"]








# def send_order_to_berna(data: str) -> dict:
#     data_dict = json.loads(data)
#     # Procesar cada producto y agregar campos faltantes
#     formatted_products = []
#     for product in data_dict.get("productList", []):
#         formatted_product = {
#             "id": 0,
#             "externalId": product.get("externalId", 0),
#             "name": product.get("name", ""),
#             "category": product.get("category", None),
#             "stock": product.get("stock", 0),
#             "moneda": None,
#             "priceIVA": product.get("priceIVA", "0"),
#             "priceSinIVA": None,
#             "isNew": True,
#             "mustSend": True
#         }
#         formatted_products.append(formatted_product)

#     # Crear orden formateada con todos los campos
#     formatted_order = {
#         "orderId": data_dict.get("orderId", ""),
#         "client": {
#             "externalId": data_dict.get("client", {}).get("externalId", ""),
#             "razonSocial": data_dict.get("client", {}).get("razonSocial", ""),
#             "cuit": data_dict.get("client", {}).get("cuit", ""),
#             "direccion": data_dict.get("client", {}).get("direccion", None),
#             "telefonos": data_dict.get("client", {}).get("telefonos", None),
#             "email": data_dict.get("client", {}).get("email", None),
#             "zona": data_dict.get("client", {}).get("zona", None)
#         },
#         "productList": formatted_products
#     }
    
#     return formatted_order
