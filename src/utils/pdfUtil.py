from langchain_community.document_loaders import PyPDFLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import os

load_dotenv()

def get_pdfs_response(question: str) -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=openai_api_key)
    pdf_path = "src/utils/pdf/InformacionEPA.pdf"

    loader = PyPDFLoader(pdf_path)
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    splits = text_splitter.split_documents(data)
    vectorstore = InMemoryVectorStore.from_documents(
        documents=splits, embedding=OpenAIEmbeddings()
    )

    retriever = vectorstore.as_retriever()

    system_prompt = (
        "Respode las preguntas de los usuarios con el contexto del pdf. Resumilas un poco para que sea mas facil de entender y leer desde WhatsApp. Si la persona pregunta por los productos que contiene la caja, reponde con la lista completa de todos ellos en forma literal."
        "Responde solo con lo que esta en el pdf, no inventes cosas."
        "Modifica el lenguaje si lo crees necesario para que suena mas natural, pero mandtene siempre el contexto del pdf."
        "Podes agregar asteriscos para resaltar palabras o frases, pero no agregues mas de 1 por lado."
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )


    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    results = rag_chain.invoke({"input": question})

    return results


