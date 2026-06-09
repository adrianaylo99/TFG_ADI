from langchain_core.messages import AIMessage
from .rag_manager import obtener_chain_rag

def nodo_educador(state, config):
    messages = state["messages"]
    
    # Se coge la última pregunta hecha por el usuario
    user_input = messages[-1].content

    # El resto el historial
    chat_history = messages[:-1]

    # Extraemos el nombre de usuario por defecto se usa Alumno
    nombre = config.get("configurable", {}).get("nombre_usuario", "Alumno")

    # Obtenemos la cadena RAG
    chain = obtener_chain_rag()
    
    # Invocamos la cadena
    # invoke devuelve un string gracias a StrOutputParser
    respuesta_texto = chain.invoke({
            "input": user_input,
            "chat_history": chat_history,
            "nombre_usuario": nombre
        },
        config=config
    )
    
    # Diccionario con la clave messages para que LangGraph lo añada al historial
    return {
        "messages": [AIMessage(content=respuesta_texto)]
    }