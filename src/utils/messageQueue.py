from collections import defaultdict
import time
import json
from utils.dbMongoUtil import get_mongo_connection  # Asegúrate de importar la función

# Cola de mensajes
message_queue = defaultdict(list)

# Tiempo de espera en segundos para procesar mensajes
MESSAGE_WAIT_TIME = 10  # Ajusta este valor según sea necesario

def add_message_to_queue(phone_number, incoming_msg):
    current_time = time.time()
    message_queue[phone_number].append((incoming_msg, current_time))
    # No procesar inmediatamente, esperar un tiempo antes de procesar
    process_message_queue(phone_number)

def process_message_queue(phone_number):
    """Procesa los mensajes en la cola para un número de teléfono específico."""
    current_time = time.time()
    messages_to_process = []  # Lista para acumular mensajes a procesar

    print(f"Procesando cola para {phone_number}. Mensajes en cola: {message_queue[phone_number]}")

    # Verificar si hay mensajes en la cola
    if message_queue[phone_number]:
        # Obtener el timestamp del primer mensaje en la cola
        first_timestamp = message_queue[phone_number][0][1]
        if current_time - first_timestamp < MESSAGE_WAIT_TIME:
            print("Reiniciando temporizador, no procesando aún.")
            return  # No procesar si el primer mensaje es reciente


    while message_queue[phone_number]:
        msg, timestamp = message_queue[phone_number][0]
        if current_time - timestamp >= MESSAGE_WAIT_TIME:
            messages_to_process.append(msg)  # Acumular solo el mensaje
            message_queue[phone_number].pop(0)  # Eliminar el mensaje procesado
        else:
            break  # Salir si no ha pasado el tiempo de espera

    # Unir todos los mensajes acumulados en un solo string
    if messages_to_process:
        combined_message = " ".join(messages_to_process)  # Combinar mensajes
        handle_message(combined_message, phone_number)  # Procesar el mensaje combinado


def handle_message(incoming_msg, phone_number):
    # Lógica para manejar el mensaje
    print(f"Procesando mensaje de {phone_number}: {incoming_msg}")

    try:
        # Actualizar el historial de conversación en MongoDB
        users_collection = get_mongo_connection('users')
        
        # Obtener el historial actual del usuario
        current_user = users_collection.find_one({"phone_number": phone_number})
        
        if current_user and "conversation" in current_user:
            # Concatenar el mensaje si ya hay un historial
            new_content = current_user["conversation"]["content"] + " " + incoming_msg
        else:
            # Si no hay historial, simplemente usar el mensaje entrante
            new_content = incoming_msg
        
        # Actualizar el historial de conversación
        users_collection.update_one(
            {"phone_number": phone_number},
            {"$set": {"conversation": {"role": "user", "content": new_content.strip()}}}
        )
        print(f"Historial de conversación actualizado para {new_content}")
        print(f"Historial actual: {current_user['conversation'] if current_user else 'No existe usuario'}")
    except Exception as e:
        print(f"Error al actualizar la base de datos: {e}")  # Mensaje de error

