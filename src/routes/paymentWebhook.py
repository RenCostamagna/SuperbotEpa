from flask import Blueprint, request
from dotenv import load_dotenv
import os

load_dotenv()

from utils.emailUtil import send_email
from utils.pedidosUtil import send_order_to_api

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from utils.dbMongoUtil import get_mongo_connection
from utils.twilioUtil import send_whatsapp_message

payment_webhook_bp = Blueprint('payment_webhook', __name__)
llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=os.getenv('OPENAI_API_KEY'), temperature=0.3)

@payment_webhook_bp.route('', methods=['GET'])
def payment_webhook():
    phone_number = request.args.get('phone_number')
    # Asegurarse de que el número de teléfono tenga el formato correcto
    if not phone_number.startswith('whatsapp:'):
        phone_number = 'whatsapp:' + phone_number  # Agregar 'whatsapp:' si no está presente
    # Asegurarse de que el número tenga el símbolo '+' después de 'whatsapp:'
    if not phone_number[9:].startswith('+'):
        phone_number = phone_number[:9] + '+' + phone_number[9:].lstrip()  # Agregar '+' y eliminar espacio
    print(f"Webhook recibido para el número de teléfono: {phone_number}")

    db = get_mongo_connection('users')
    user = db.find_one({"phone_number": phone_number})
    user_shipp = user.get("last_shipp", {}).get("client", [])
    user_list = user.get("productList", None)
    conversation = user.get("conversation", [])
    send_order_to_api(user_list, user_shipp, phone_number)
    send_email("pagado con payway", user_shipp, user_list)  # Esta función debe venir de utils.emailUtil

    prompt = ChatPromptTemplate.from_messages([
        ("system", "El usuario realizo un pago. Debes enviar un mensaje de agradecimiento por el pago."),
        ("placeholder", "{conversation}")
    ])

    chain = prompt | llm
    response = chain.invoke({"conversation": conversation})
    print(response.content)
    message = response.content
    db.update_one({"phone_number": phone_number}, {"$push": {"conversation": {"role": "assistant", "content": message}}})
    send_whatsapp_message(phone_number, message)
    return "OK", 200
