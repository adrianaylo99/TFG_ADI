import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import add_messages, StateGraph, END
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from agentes.educador.nodo_educador import nodo_educador
from agentes.demostrador.nodo_demostrador import nodo_demostrador
from agentes.critico.nodo_critico import nodo_critico
from agentes.evaluador.nodo_evaluador import nodo_evaluador
from utils.db_manager import pool

load_dotenv()
api_key_oss = os.getenv("GPT_OSS_KEY") 
base_url_oss = os.getenv("BASE_URL_OSS")

if not os.getenv("LANGSMITH_API_KEY"):
    print("Error al obtener la LANGSMITH_API_KEY en .env")
    exit()
if not api_key_oss:
    print("No se ha encontrado la API Key de GPT-OSS en el .env")
    exit()

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Función enrutadora que pasa el control a un agente u otro en función de la pregunta del usuario
def enrutador_agentes(state) -> Literal["educador", "demostrador", "critico", "evaluador"]:
    ultimo_mensaje = state["messages"][-1].content
    chat_history = state["messages"][:-1]

    # El enrutador necesita tener un poco el hilo de la conversación para tener mejor juicio
    # ya que los ejercicios pueden estar sacados de la teoría y a veces se confunde y llama al educador
    # cuando no debe
    historial_texto = ""
    for msg in chat_history[-6:]:
        rol = "Asistente" 
        if msg.type == "human":
            rol = "Usuario"

        historial_texto += f"{rol}: {msg.content}\n"
        
    if not historial_texto:
        historial_texto = "No hay historial previo. Es el comienzo de la conversación."
    
    llm = ChatOpenAI(
        model="gpt-oss",
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0,
        streaming=False
    )
    
    prompt_clasificador = f"""
    Eres un árbitro enrutador. 
    Tu única tarea es clasificar la intención del usuario devolviendo ÚNICAMENTE la palabra 'educador', 'demostrador', 'critico' o 'evaluador'.

    REGLAS ESTRICTAS:
    - Responde 'educador' si el usuario pide explicaciones teóricas, conceptos nuevos o hacer preguntas generales.
    - Responde 'demostrador' si el usuario pide ver un código, un ejemplo práctico, o está interactuando con opciones (A, B...) de un ejemplo.
    - Responde 'critico' si el usuario envía código y/o pide que se le corrija.
    - Responde 'evaluador' si el usuario envía código y/o pide que se puntúe.
    - En caso de que la petición del usuario no corresponda a ninguna de las anteriores simplemente responde 'educador'
    - REGLA DE CONTEXTO CLAVE: Lee el historial para verificar qué quiere exactamente el usuario. Si entre los últimos mensajes 
    el 'Asistente' le ha ofrecido un ejemplo o le ha pedido que elija un tema práctico, y el usuario responde a ese mensaje con 
    el tema o ejemplo que desea, debes responder 'demostrador', ya que está continuando el flujo práctico.

    HISTORIAL RECIENTE:
    {historial_texto}

    MENSAJE ACTUAL DEL USUARIO:
    Usuario: {ultimo_mensaje}
    """
    
    respuesta = llm.invoke([SystemMessage(content=prompt_clasificador)])
    decision = respuesta.content.strip().lower()

    return decision if decision in ["educador", "demostrador", "critico", "evaluador"] else "educador"

def obtener_grafo():
      
    graph = StateGraph(State)
    graph.add_node("educador", nodo_educador)
    graph.add_node("demostrador", nodo_demostrador)
    graph.add_node("critico", nodo_critico)
    graph.add_node("evaluador", nodo_evaluador)

    graph.set_conditional_entry_point(
        enrutador_agentes,
        {
            "educador": "educador",
            "demostrador": "demostrador",
            "critico": "critico",
            "evaluador": "evaluador"
        }
    )

    graph.add_edge("educador", END)
    graph.add_edge("demostrador", END)
    graph.add_edge("critico", END)
    graph.add_edge("evaluador", END)

    # Los checkpoints se almacenan en una BD y con el setup() forzamos que se creen
    # las tablas si no existían
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()

    app = graph.compile(checkpointer=checkpointer)
    
    return app