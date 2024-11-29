# src/utils/twilioUtil.py

from twilio.rest import Client
from dotenv import load_dotenv

import os

load_dotenv()

# Configuraciones de Twilio
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_NUMBER')

client = Client(account_sid, auth_token)

def send_whatsapp_message(phone_number, message):
    # Límite de caracteres de Twilio
    char_limit = 1600  # Ajusta este valor según el límite de Twilio
    messages = [message[i:i + char_limit] for i in range(0, len(message), char_limit)]
    
    for msg in messages:
        client.messages.create(
            body=msg,
            from_=f'{twilio_number}',
            to=phone_number
        )
    
    return len(messages)  # Retorna la cantidad de mensajes enviados

