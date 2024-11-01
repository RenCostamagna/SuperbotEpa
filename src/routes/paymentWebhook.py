from flask import Blueprint, request
import os
from dotenv import load_dotenv
load_dotenv()   

from utils.twilioUtil import send_whatsapp_message

payment_webhook_bp = Blueprint('payment_webhook', __name__)


@payment_webhook_bp.route('', methods=['POST'])
def payment_webhook():
    phone_number = request.args.get('phone_number')
    print(f"Webhook recibido para el número de teléfono: {phone_number}")
    send_whatsapp_message(phone_number, "El pago fue realizado correctamente!")
    return "OK", 200
