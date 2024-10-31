from flask import Blueprint, request

payment_webhook_bp = Blueprint('payment_webhook', __name__)

@payment_webhook_bp.route('', methods=['POST'])
def payment_webhook():
    print("Webhook recibido")
    return "OK", 200
