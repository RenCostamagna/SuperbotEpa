from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_mongo_connection(collection_name):
    """
    Función para conectarse a MongoDB y devolver la base de datos y la colección de usuarios.
    """
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri)
    
    # Nombre de la base de datos y colección
    db = client['EPA']
    users_collection = db[collection_name]
    
    return users_collection
