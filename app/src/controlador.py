from langchain_core.messages import HumanMessage
from utils import db_manager
from grafos.grafo_agentes import obtener_grafo

# Instanciamos el grafo una sola vez
app_grafo = obtener_grafo()

# Busca o crea al usuario y devuelve su ID
def login_usuario(username: str) -> str:
    return db_manager.obtener_o_crear_usuario(username)

# Devuelve la lista de chats del usuario
def obtener_chats(user_id: str) -> list:
    return db_manager.obtener_chats_usuario(user_id)

# Crea un nuevo chat y devuelve el thread_id
def crear_chat(user_id: str) -> str:
    return db_manager.crear_nuevo_chat(user_id)

# Si el chat es nuevo, genera un título basado en el prompt
def renombrar_chat_si_aplica(thread_id: str, prompt: str, chats: list):
    for c in chats:
        if c["thread_id"] == thread_id and c["titulo"] == "Nueva conversación":
            nuevo_titulo = prompt[:25] + "..." if len(prompt) > 25 else prompt
            db_manager.actualizar_titulo_chat(thread_id, nuevo_titulo)
            break

# Recupera los mensajes guardados en el grafo para un chat específico
def obtener_historial_chat(thread_id: str, username: str) -> list:
    config = {"configurable": {
        "thread_id": thread_id, 
        "nombre_usuario": username
        }
    }
    estado = app_grafo.get_state(config)
    if hasattr(estado, 'values') and "messages" in estado.values:
        return estado.values["messages"]
    return []

# Ejecuta el grafo con la nueva petición y devuelve la respuesta final
def procesar_mensaje(prompt: str, thread_id: str, username: str, stream_handler) -> str:
    config = {
        "configurable": {
            "thread_id": thread_id,
            "nombre_usuario": username
        },
        # Inyectamos el streaming
        "callbacks": [stream_handler]
    }
    
    initial_state = {"messages": [HumanMessage(content=prompt)]}

    # El mensaje del alumno se guarda en la bd
    db_manager.agregar_mensaje_texto_plano(thread_id, "ALUMNO", prompt)
    
    # Ejecutamos el grafo el stream_handler se encarga de pintar
    for _ in app_grafo.stream(initial_state, config=config):
        pass 
        
    # Recuperamos el mensaje final real de LangGraph
    estado_final = app_grafo.get_state(config)
    respuesta_final = estado_final.values["messages"][-1].content

    # Guardamos la respuesta del sistema en el texto plano manual
    db_manager.agregar_mensaje_texto_plano(thread_id, "ADI", respuesta_final)

    return respuesta_final