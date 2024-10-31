# src/main.py
import os
from flask import Flask
from routes.messageWebhook import message_webhook_bp
from routes.paymentWebhook import payment_webhook_bp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.register_blueprint(message_webhook_bp, url_prefix='/webhook')
app.register_blueprint(payment_webhook_bp, url_prefix='/payment')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', debug=True, port=port)

