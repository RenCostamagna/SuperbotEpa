from flask import Blueprint, request
import os
import requests
import openai
import json
import redis

#Importaciones de utils
from utils.twilioUtil import send_whatsapp_message
from utils.dbMongoUtil import get_mongo_connection
from utils.productsUtil import fetch_products_from_api
from utils.clientsUtil import fetch_clients_from_api
from utils.pdfUtil import get_pdfs_response
from utils.emailUtil import send_email
from utils.pedidosUtil import send_order_to_api
from utils.paymentUtil import send_payment_intentions_to_api
from config.getExternalId import get_external_id

#Importaciones de Langchain
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool
from langchain_core.prompts import ChatPromptTemplate

from requests.auth import HTTPBasicAuth

from dotenv import load_dotenv
load_dotenv()

twilio_auth = HTTPBasicAuth(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

#Conexion a Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

message_webhook_bp = Blueprint('message_webhook', __name__)
#    - No uses negritas. Tene en cuenta que la aplicacion se despliega en whatsapp, y las negritas son con un asterisco para cada lado de la palabra.
openai.api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=os.getenv('OPENAI_API_KEY'), temperature=0.3)

template = """
    Sos un ayudante de ventas de WhatsApp. Tu tarea es ayudar a los usuarios a realizar sus compras y responder preguntas acerca la EPA (Empresa Publica de Alimentos). No brindes informacion sobre otros temas.

    **Reglas de Formato**
    - Usa asteriscos alrededor de *nombres de productos* y *montos totales* para facilitar la lectura en WhatsApp.
    - Indica los precios con el signo $ y no coleques comas para separar los miles. Por ejemplo: $17500 y no $17,500.
    - Si la persona solicita un producto, devuélvelo en forma de lista para facilitar la lectura; incluye la cantidad y el total si es más de uno del mismo producto.
    - No uses negritas, ya que en WhatsApp se marcan con asteriscos.
    
    **Tono y Lenguaje**:
    - Usa un lenguaje claro, amigable y regional: "tenés", "querés", "son", "vendemos", "sos", "acá".
    - Varía tus respuestas para mantener una conversación amena y parecer parte de la empresa.
    
    **Preguntas sobre la empresa: API de PDF**
    - Siempre que la persona pida que productos contiene la caja, usa la herramienta de consulta al PDF para responder y devolve todoos ellos.
    - Si el usuario pregunta sobre la empresa, utiliza la herramienta de consulta al PDF para responder.
    - No des precios que esten dentro del PDF.
    - Las recetas estan dentro del archivo.

    **Manejo de Inventario**:
    - Responde solo sobre productos en stock; verifica cantidades suficientes.
    - Si el usuario quiere comprar, usa la herramienta *inventory* para encontrar el producto.
    - Ante preguntas amplias sobre productos, muestra todas las opciones disponibles.
    - No reveles el stock actual, solo confirma disponibilidad.

    **Puntos de retiro**
    - D1: Uriburu 1074 (de 10:00 hs a 16:00 hs) 
    - D5: Rondeau 2101 (de 10:00 hs a 16:00 hs)
    - D6: San Martin 1168 (de 10:00 hs a 18:00 hs)
    - La Lactería: Av Alberdi 445 (de 9:00 hs a 13.30 hs y de 16:00 hs a 20.30 hs)

    **Confirmacion del pedido**
    Para la confirmacion segui los siguientes pasos: 
    1. Preguntale al usuario si quiere confirmar el pedido antes de seguir.
    2. Cuando el cliente confirme el pedido, ofrecele al usuario los puntos de retiro para que elija uno y aclarale que se retiran el miercoles 6 de noviembre.
    3. Una vez elija uno, usa la herramienta product_order_data con los nombres de los productos y la cantidad que compro para guardar los id en la lista de productos. POr ejemplo: "2 caja epa n1".
    4. Una vez confirmado el pedido, solicitale el nombre, apellido y DNI/CUIT.
    5. Cuando tengas estos datos, guarda los datos del usuario con la herramienta de user_order_data.
    6. Una vez hecho eso, preguntale al cliente si quiere pagar el pedido por transferencia bancaria o a travez de Payway. Estos son los unicos medios de pago. Si el usuario paga por Payway, no uses la herramienta send_email_tool.
    
    **Pago**
    - Si la persona paga con transferencia bancaria:
        1. Envia el alias y el cbu para que la persona pueda pagar, e indicale que cuando retire el pedido tiene que mostrar el comprobante. 
            - Los datos son estos: Titular: COOP DE TRAB ALIMENTOS SOB LT, CBU: 19102748-55027402367700, Alias: epa.rosario.
        2. Usa la herramienta send_email_tool para enviar un mail con el estado "transferencia" del pedido. No esperes a que pague el usuario para usar la herramienta. No le des informacion acerca de mail al usuario, ya que son para uso interno.
    - Si la persona paga con Payway: 
        1. Usa la herramienta send_payment_intention para enviar el link de pago al usuario de forma clara. No incluyas el link adentro de una palabra.
    
    **Finalizacion del pedido**
    - Una vez se haya enviado la correspondiente confirmacion, pregunta al usuario si quiere seguir comprando o si necesita ayuda con algo mas.
    - Si la respuesta es que no, envia un mensaje de despedida y llama a la herramienta de cancel_order para reiniciar el historial de la conversacion.

    **Cancelación del Pedido**
    - Si el cliente quiere cancelar, pregunta si está seguro.

    **Notas Adicionales**
    - La empresa no realiza envios a domicilio.
    - Si piden el producto más barato o más caro, asegúrate de que lo sea.
    - Si alguna persona pregunta acerca de algun empleado, indicale que sos un bot y que no tenes informacion sobre los empleados.
    - Tene en cuenta que dentro de los productos que vendemos hay cajas de productos, nombradas como "caja 1" por ejemplo.
    - Si lo creer necesario, usa mas de una herramienta para responder la pregunta.
    """

@message_webhook_bp.route('', methods=['POST'])
def message_webhook():
    #Recibo el contenido del mensaje y el número de teléfono
    print("Webhook recibido")
    incoming_msg = request.form.get('Body', "")
    audio_url = request.form.get('MediaUrl0', "")
    phone_number = request.form['From']
    print(phone_number)

    if audio_url:
        print(f"Audio recibido: {audio_url}")
        incoming_msg = transcribe_audio_with_whisper(audio_url)
    
    #Guardar el mensaje en Redis
    redis_client.rpush("message_queue", f"{phone_number}|{incoming_msg}")

    #Leer el mensaje de Redis
    print("Leyendo mensaje de Redis")
    message = redis_client.lpop("message_queue")
    if message:
        message = message.decode("utf-8")
        phone_number, incoming_msg = message.split("|", 1)
    else:
        print("No hay mensajes en la cola")  # Manejo de caso cuando no hay mensajes

    #Clear cache
    if incoming_msg.lower() == "clear":
        users_collection = get_mongo_connection('users')
        users_collection.update_one(
            {"phone_number": phone_number},
            {"$set": {"conversation": [], "last_shipp": {"orderId": 0, "client": []}, "productList": []}}
        )
        send_whatsapp_message(phone_number, "Historial de conversacion reiniciado")
        return "Historial de conversacion reiniciado"
    
    #Buscar usuario en la base de datos
    print("buscando usuario en la base de datos")
    users_collection = get_mongo_connection('users')
    print("usuario encontrado")
    user = users_collection.find_one({'phone_number': phone_number})
    print(user)

    principalPrompt = ChatPromptTemplate.from_messages([
        ("system", template),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    #Herramienta de consulta de PDF
    @tool
    def pdf_query(input: str) -> str:
        """Usa esta herramienta para obtener la información de la empresa."""
        return get_pdfs_response(input)

    #Herramienta de inventario
    @tool
    def inventory() -> list:
        """Usa esta herramienta para obtener los productos que solicita el usuario y ver cuales estan disponibles."""
        products = fetch_products_from_api()
        return products
    
    #Herramienta de envio de mail
    @tool
    def send_email_tool(input: str) -> str:  # Cambié el nombre para evitar conflicto
        """Envia un mail con el estado del pedido pago por transferencia."""
        users_collection = get_mongo_connection('users')
        user = users_collection.find_one({'phone_number': phone_number})
        user_shipp = user.get("last_shipp", {}).get("client", [])
        user_list = user.get("productList", None)
        send_order_to_api(user_list, user_shipp, phone_number)
        send_email(input, user_shipp, user_list)  # Esta función debe venir de utils.emailUtil
        return input

    #Herramienta de consulta de cliente
    @tool
    def client_data() -> list:
        """Realiza una llamada a la API para verificar si el cliente esta registrado en la base de datos a travez de la razon social o el nombre y apellido."""
        clients = fetch_clients_from_api()
        return clients
    
    #Herramienta de envio de link pago
    @tool
    def send_payment_intention(input: str) -> str:
        """Envia el link de pago al usuario de forma clara. No incluyas el link adentro de una palabra."""
        users_collection = get_mongo_connection('users')
        user = users_collection.find_one({'phone_number': phone_number})
        user_shipp = user.get("last_shipp", {}).get("client", [])
        user_list = user.get("productList", None)
        url = send_payment_intentions_to_api(user_shipp, user_list, phone_number)
        return url

    #Herramienta de guardado de datos del cliente
    @tool
    def user_order_data(input: list) -> str:
        """Guarda los datos del cliente en last_shipp. Los datos que tenes que guarda son los que le solicitaste al usuario. 
        El formato de last_shipp es el siguiente:"externalId": 0,"razonSocial": "dato dado por el usuario","cuit":"dato dado por el usuario cuit o dni","retiro":"punto de retiro elegido por el usuario".
        En razonSocial, guarda nombre y apellido.
        Al usuario guardalo como una lista con el diccionario adentro.
        """
        if isinstance(input, dict):
            input = json.dumps(input)
            print("input es un diccionario", input)
        users_collection = get_mongo_connection('users')
        users_collection.update_one(
            {"phone_number": phone_number},
            {"$set": {"last_shipp.client": input}}
        )
        return input
    
    #Herramienta de guardado de externalId de los productos del pedido
    @tool
    def product_order_data(input: str) -> str:
        """Guarda los externalId de los productos del pedido en productList. 
        """
        products = fetch_products_from_api()
        print("productos", products)
        response = get_external_id(input, products)
        print("response", response)
        users_collection = get_mongo_connection('users')
        users_collection.update_one(
            {"phone_number": phone_number},
            {"$set": {"productList": response}}
        )
        return response

    #Herramienta de cancelacion de orden
    @tool
    def cancel_order(input: str) -> str:
        """Cancela una orden en curso, asegurate de haber preguntado al usuario si esta seguro de cancelar la orden antes de ejecutar la accion"""
        users_collection = get_mongo_connection('users')
        
        #Obtengo el historial de la conversacion actual
        user = users_collection.find_one({'phone_number': phone_number})
        current_conversation = user.get("conversation", [])

        #Actualizo el historial de la conversacion actual
        users_collection.update_one(
            {"phone_number": user["phone_number"]},  # Asegúrate de tener el número de teléfono disponible
            {"$set": { "last_shipp": {}, "productList": []}}  # Limpia los campos deseados
        )
        return f"{input}"
    
    tools = [inventory, cancel_order, client_data, pdf_query, send_email_tool, user_order_data, product_order_data, send_payment_intention]

    agent = create_tool_calling_agent(llm, tools, principalPrompt)
    print("buscando historial de conversacion")
    # Obtener el historial de conversación, creando el usuario si no existe
    if user:
        chat_history = user.get("conversation", [])
    else:
        # Crear un nuevo usuario si no existe
        users_collection.insert_one({
            "phone_number": phone_number,
            "conversation": [{"role": "user", "content": incoming_msg}],    
            "id_cliente": None,
            "last_conversation": [],
            "productList": [],
            "total": None,
            "last_shipp": {
                "orderId": 0,
                "client": []
            }
        })
        print("Usuario creado y conversación iniciada")
        chat_history = []  # Inicializar el historial de conversación vacío
    
    print("historial de conversacion encontrado")

    # Continuar con el flujo de generación de respuesta
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    response = agent_executor.invoke({"input": f"{incoming_msg}", 
                                      "chat_history": chat_history})
    # Genero la cadena con el prompt y el modelo de lenguaje
    print(response)
    # Formateo la respuesta para enviarla por WhatsApp
    contentResponse = response["output"]
    messageResponse = send_whatsapp_message(phone_number, contentResponse)
    
    users_collection.update_one(
        {"phone_number": phone_number},
        {"$push": {"conversation": {"role": "user", "content": incoming_msg}}}
    )
    users_collection.update_one(
        {"phone_number": phone_number},
        {"$push": {"conversation": {"role": "assistant", "content": contentResponse}}}
    )
    print(messageResponse)
    return "Mensaje enviado"


def transcribe_audio_with_whisper(audio_url):
    try:
        # Usar stream=True para manejar archivos grandes de manera más eficiente
        audio_response = requests.get(audio_url, auth=twilio_auth, stream=True)
        audio_response.raise_for_status()
        
        temp_file = "audio_received.ogg"
        with open(temp_file, "wb") as audio_file:
            # Descargar en chunks para mejor manejo de memoria
            for chunk in audio_response.iter_content(chunk_size=8192):
                if chunk:
                    audio_file.write(chunk)
        
        # Usar Whisper para transcribir el audio
        with open(temp_file, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"  # Especificar formato de respuesta para mayor velocidad
            )
        
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return transcript

    except requests.RequestException as e:
        print(f"Error al descargar el audio: {str(e)}")
        return "Error al descargar el archivo de audio"
    except openai.OpenAIError as e:
        print(f"Error en la transcripción: {str(e)}")
        return "Error al transcribir el audio"
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return "Error al procesar el audio"
    finally:
        # Asegurar que el archivo temporal se elimine incluso si hay errores
        if os.path.exists("audio_received.ogg"):
            os.remove("audio_received.ogg")

