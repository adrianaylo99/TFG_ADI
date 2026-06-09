import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from dotenv import load_dotenv

MD_FOLDER_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "Teoria")
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "utils", "ChromaDB")
COLLECTION_NAME = "demo_agente_educador"

load_dotenv()
api_key_oss = os.getenv("GPT_OSS_KEY") 
base_url_oss = os.getenv("BASE_URL_OSS")

if not os.getenv("LANGSMITH_API_KEY"):
    print("Error al obtener la LANGSMITH_API_KEY en .env")
    exit()
if not api_key_oss:
    print("No se ha encontrado la API Key de GPT-OSS en el .env")
    exit()

# Lee los archivos Markdown los divide semánticamente por sus títulos y crea o actualiza la base de datos vectorial
def indexar_documentos_en_ChromaDB():

    if not os.path.exists(MD_FOLDER_PATH):
        return None

    documentos_divididos = []

    # Jerarquía del Markdown
    headers_to_split_on = [
        ("#", "Tema"),
        ("##", "Seccion"),
        ("###", "Subseccion"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on,
                                                   strip_headers=False 
    )

    # Splitter secundario
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, 
        chunk_overlap=100
    )

    for archivo in os.listdir(MD_FOLDER_PATH):
        if archivo.endswith(".md"):
            ruta_md = os.path.join(MD_FOLDER_PATH, archivo)
            
            with open(ruta_md, "r", encoding="utf-8") as f:
                texto_markdown = f.read()

            # Agrupa por títulos
            md_docs = markdown_splitter.split_text(texto_markdown)

            # División por tamaño máximo
            splits_finales = text_splitter.split_documents(md_docs)
            
            # Limpieza de metadatos
            for doc in splits_finales:
                claves_a_borrar = [k for k in doc.metadata.keys() if k not in ["Tema", "Seccion", "Subseccion"]]
                for k in claves_a_borrar:
                    del doc.metadata[k]
                    
            documentos_divididos.extend(splits_finales)

    if not documentos_divididos:
        return None

    # Le decimos que busque Ollama en una variable de entorno y si no existe en localhost
    # Necesario para docker
    url_ollama = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=url_ollama)

    vector_store = Chroma.from_documents(
        collection_name=COLLECTION_NAME,
        documents=documentos_divididos,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )

    return vector_store

def formatear_documentos(docs):
    text_block = "\n\n".join(doc.page_content for doc in docs)
    return text_block

# Configura y devuelve la cadena RAG lista para ser consultada.
def obtener_chain_rag():

    # Se busca Ollama en una variable de entorno y si no existe en localhost
    # Esto es para el contenedor docker
    url_ollama = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=url_ollama)
    
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_PATH, 
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME)

    numero_documentos = vectorstore._collection.count()

    if numero_documentos == 0:
        # Indexación y se sobrescribe el vectorstore con los datos nuevos
        vectorstore = indexar_documentos_en_ChromaDB()

    # Configurar el Retriever
    # k=6 significa que recuperará los 6 fragmentos más relevantes
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

    # Configurar el LLM
    llm = ChatOpenAI(
        model="gpt-oss",
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0.1,
        streaming=True
    )

    # Prompt que solo use información del contexto
    system_prompt = (
        "Eres un profesor de programación experto, paciente y didáctico.\n"
        "Tu objetivo es ayudar al alumno {nombre_usuario} a comprender conceptos básicos.\n"
        "\n"
        "### INSTRUCCIONES DE RESPUESTA:\n"
        "1. BASADO EN HECHOS: Responde ÚNICAMENTE usando la información del Contexto proporcionado abajo. "
        "Si la respuesta no está en el contexto, di amablemente: 'Lo siento, no tengo esa información en mis apuntes actuales', no intentes inventarla.\n"
        "2. TONO: Sé amable y motivador. No menciones 'el contexto' ni 'los documentos'. Habla como si fuera tu propio conocimiento.\n"
        "3. FORMATO: Si muestras código, usa SIEMPRE bloques de código Markdown (```cpp ... ``` o ```pseudocodigo ... ```) para que se vea bien.\n"
        "4. IDIOMA: Responde siempre en Español, incluso si el código del contexto está en inglés.\n"
        "\n"
        "### CONTEXTO:\n"
        "{context}"
    )

    # Le damos al LLM primero el system promt, luego el historial para que tenga memoria y por último el input
    # del usuario
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])

    # Crear la cadena RAG
    qa_chain = (
        {
            "context": (lambda x: x["input"]) | retriever | formatear_documentos,
            "input": lambda x: x["input"],
            "chat_history": lambda x: x["chat_history"],
            "nombre_usuario": lambda x: x["nombre_usuario"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return qa_chain