from dotenv import load_dotenv
import ast
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import os
load_dotenv()

def get_external_id(product_name: str, inventory: list) -> list:
    print("product_name", product_name)
    print("inventory", inventory)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=openai_api_key)
    inventory_str = "\n".join(str(item) for item in inventory)
    print("inventory_str", inventory_str)
    system_prompt = (
        """Eres un asistente especializado en buscar productos en un inventario.
        Tu tarea es encontrar y extraer la información exacta del producto solicitado.
        
        Inventario disponible:
        {inventory}
        
        Devolve unicamente el externalId, el articulo_descripcion, el stock(cantidad que compro el usuario, no lo extraigas del inventario), el rubro y el con_iva de cada uno de los productos que encontraste. No des informacion adicional.
        Guarda unicamente los productos solicitados por el usuario. Si el usuario solicito dos o mas productos del mismo, guarda solo uno.
        La respuesta tiene que ser una lista de diccionarios.
        """
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm

    results = chain.invoke({
        "input": product_name,
        "inventory": inventory_str
    })
    print("results", results.content)
    results_list = ast.literal_eval(results.content)
    print("results_list", results_list)
    print("type", type(results_list))

    return results_list



