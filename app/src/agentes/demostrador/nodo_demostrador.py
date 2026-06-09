import os
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from utils.funciones_auxiliares import cargar_rubrica_demostrador
from dotenv import load_dotenv


load_dotenv()
api_key_oss = os.getenv("GPT_OSS_KEY") 
base_url_oss = os.getenv("BASE_URL_OSS")

def nodo_demostrador(state, config):
    messages = state["messages"]
    chat_history = messages[:-1]
    user_input = messages[-1].content
    ejemplos = cargar_rubrica_demostrador()

    historial_solo_usuario =[msg for msg in chat_history if msg.type == "human"]

    # Para no sobrecargar de tokens hay una búsqueda en 2 pasos
    # Primero usamos el llm para que use el mensaje del alumno y busque el título del ejemplo
    # que quiere de entre todos los títulos del JSON.

    # Usamos un catálogo que tenga la clave y el título de todos los elementos del JSON
    item_list = {k: v["tema"] for k, v in ejemplos.items()}

    llm_buscador = ChatOpenAI(
        model="gpt-oss",
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0
    )

    prompt_buscador = f"""
    Eres un bibliotecario. Lee el historial y el mensaje actual del usuario.
    Aquí tienes nuestro catálogo de ejemplos disponibles:
    {json.dumps(item_list, ensure_ascii=False, indent=2)}

    Reglas:
    1. Si el usuario pide un ejemplo sobre un tema, devuelve ÚNICAMENTE la clave (el ID) del ejemplo que mejor encaje.
    2. Si el usuario pide la "Opción A", "B", etc., revisa el historial para saber de qué clave estabais hablando y devuelve esa misma clave.
    3. Si pide algo que NO está en el catálogo, no escribas nada.
    
    No escribas ninguna explicación, SOLO la clave o nada.
    """
    
    mensajes_buscador =[SystemMessage(content=prompt_buscador)] + historial_solo_usuario + [HumanMessage(content=user_input)]
    
    # Obtenemos la ID exacta del ejercicio
    id_encontrado = llm_buscador.invoke(mensajes_buscador).content.strip()


    
    # Instanciamos el LLM
    llm = ChatOpenAI(
        model="gpt-oss",
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0.2,
        streaming=True
    )

    ejemplo_seleccionado = ejemplos.get(id_encontrado)

    if ejemplo_seleccionado:
        info_json = json.dumps(ejemplo_seleccionado, ensure_ascii=False, indent=2)
        system_prompt = f"""
        Eres el Agente Demostrador. Tu objetivo es enseñar código paso a paso.
        Aquí tienes la información EXCLUSIVA del ejemplo que debes mostrar:
        
        {info_json}
        
        REGLAS:
        1. Si es la primera vez que habláis de este ejemplo, muéstrale el 'codigo_correcto' y la 'explicacion'. 
        2. Luego, ofrécele las 'variantes' (ej: "¿Qué pasa si nos saltamos el primer elemento? Responde A para verlo"). NO le digas el error todavía.
        3. Si el alumno ha respondido 'A' y/o 'B' a un ejemplo anterior, muéstrale el código de esa(s) variante(s) y usa el campo 'error' para explicarle por qué fallaría.
        4. Usa siempre bloques de código Markdown (```) para el código.
        """
    else:
        # Por si pide algo que no está en el catálogo
        lista_temas = "\n".join([f"- {v}" for v in item_list.values()])
        system_prompt = f"""
        Eres el Agente Demostrador.
        El usuario ha pedido un ejemplo, pero no tenemos ninguno exacto en la base de datos sobre eso. 
        Ofrécele amablemente elegir entre los temas que sí tenemos disponibles:
        \n{lista_temas}
        """

    # El mensaje del sistema convertido en una cadena
    system_message = SystemMessage(content=system_prompt)
    
    # El mensaje del usuario
    current_message = HumanMessage(content=user_input)
    
    # Lista con todo para que el llm lo reciba
    llm_message = [system_message] + chat_history + [current_message]
    
    # Llamada directa al llm con el mensaje y el config para el streming de tokens
    respuesta = llm.invoke(llm_message, config=config)
    
    # Devolvemos el estado actualizado
    return {"messages": [AIMessage(content=respuesta.content)]}
    
