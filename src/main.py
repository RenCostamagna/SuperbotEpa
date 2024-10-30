# src/main.py
import os
from flask import Flask
from routes.messageWebhook import message_webhook_bp
from dotenv import load_dotenv
from pymongo import MongoClient
import datetime

load_dotenv()

app = Flask(__name__)

app.register_blueprint(message_webhook_bp, url_prefix='/webhook/')

# Conexión a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['EPA']
logs_collection = db['items']

# Función para registrar el log
def log_startup():
    log_entry = {
        'message': 'La aplicación ha sido iniciada',
        'timestamp': datetime.datetime.now()
    }
    logs_collection.insert_one(log_entry)

# Llamar a la función de log al iniciar la aplicación
log_startup()

if __name__ == '__main__':
    app.run(debug=True)

