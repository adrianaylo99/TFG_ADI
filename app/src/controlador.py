import traceback
from langchain_core.messages import HumanMessage
from utils import db_manager
from grafos.grafo_agentes import obtener_grafo

# Instanciamos el grafo una sola vez
app_grafo = obtener_grafo()

# Busca o crea al usuario y devuelve su ID
def login_usuario(username: str) -> str:
    try:
        return db_manager.obtener_o_crear_usuario(username)
    except Exception as e:
        print(f"Error BD login: {e}")
        raise e 

# Devuelve la lista de chats del usuario
def obtener_chats(user_id: str) -> list:
    try:
        return db_manager.obtener_chats_usuario(user_id)
    except Exception as e:
        print(f"Error BD obtener chats: {e}")
        return []

# Crea un nuevo chat y devuelve el thread_id
def crear_chat(user_id: str) -> str:
    try:
        return db_manager.crear_nuevo_chat(user_id)
    except Exception as e:
        print(f"Error BD crear chat: {e}")
        raise e

# Si el chat es nuevo, genera un título basado en el prompt
def renombrar_chat_si_aplica(thread_id: str, prompt: str, chats: list):
    try:
        for c in chats:
            if c["thread_id"] == thread_id and c["titulo"] == "Nueva conversación":
                nuevo_titulo = prompt[:25] + "..." if len(prompt) > 25 else prompt
                db_manager.actualizar_titulo_chat(thread_id, nuevo_titulo)
                break
    except Exception as e:
        print(f"Error BD al actualizar título del chat: {e}")
        pass

# Recupera los mensajes guardados en el grafo para un chat específico
def obtener_historial_chat(thread_id: str, username: str) -> list:
    try:
        config = {"configurable": {
            "thread_id": thread_id, 
            "nombre_usuario": username
            }
        }
        estado = app_grafo.get_state(config)
        if hasattr(estado, 'values') and "messages" in estado.values:
            return estado.values["messages"]
        return []
    except Exception as e:
        print(f"Error al obtener historial: {e}")
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
    try:
        db_manager.agregar_mensaje_texto_plano(thread_id, "ALUMNO", prompt)
    except Exception as e:
        print(f"Error al guardar mensaje del usuario en el historial local: {e}")
        pass
    
    try:
        # Ejecutamos el grafo el stream_handler se encarga de pintar
        for _ in app_grafo.stream(initial_state, config=config):
            pass 
            
        # Recuperamos el mensaje final real de LangGraph
        estado_final = app_grafo.get_state(config)
        respuesta_final = estado_final.values["messages"][-1].content

        # Guardamos la respuesta del sistema en el texto plano manual
        try:
            db_manager.agregar_mensaje_texto_plano(thread_id, "ADI", respuesta_final)
        except Exception as e:
            print(f"Error al guardar mensaje del sistema en el historial local: {e}")
            pass

        return respuesta_final
    
    except Exception as e:
        print("Error crítico del Grafo/BD: ", e)
        traceback.print_exc() 
        return "**Aviso del sistema:** Error crítico de conexión con la base de datos. Por favor, inténtalo más tarde."