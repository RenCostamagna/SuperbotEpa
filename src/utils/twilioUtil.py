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
    message = client.messages.create(
        body=message,
        from_=f'{twilio_number}',
        to=phone_number
    )
    return message.sid

