import os
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from utils.funciones_auxiliares import cargar_rubrica_demostrador
from dotenv import load_dotenv


load_dotenv()
model_name = os.getenv("OPENAI_MODEL_NAME")
api_key_oss = os.getenv("GPT_OSS_KEY") 
base_url_oss = os.getenv("BASE_URL_OSS")

def nodo_demostrador(state, config):
    messages = state["messages"]
    chat_history = messages[:-1]
    user_input = messages[-1].content
    ejemplos = cargar_rubrica_demostrador()

    if not ejemplos:
        error_msg = "**Aviso del sistema:** Lo siento, el sistema no se encuentra disponible por un problema técnico en el servidor. Avise a un administrador."
        return {"messages": [AIMessage(content=error_msg)]}

    # Para no sobrecargar de tokens hay una búsqueda en 2 pasos
    # Primero usamos el llm para que use el mensaje del alumno y busque el título del ejemplo
    # que quiere de entre todos los títulos del JSON.

    # Usamos un catálogo que tenga la clave y el título de todos los elementos del JSON
    item_list = {k: v["tema"] for k, v in ejemplos.items()}

    llm_buscador = ChatOpenAI(
        model=model_name,
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0,
        max_tokens=3000
    )

    prompt_buscador = f"""
    Eres un bibliotecario estricto. Analiza el historial de la conversación y el mensaje actual del usuario.
    
    CATÁLOGO DE EJEMPLOS:
    {json.dumps(item_list, ensure_ascii=False, indent=2)}

    TU TAREA:
    1. Si el usuario pide un ejemplo sobre un tema, busca en el CATÁLOGO y devuelve ÚNICAMENTE la clave (ID) del ejemplo correspondiente.
    2. Si el usuario pide una variante (como "Opción A", "Quiero la B", etc.), revisa el historial para saber de qué ejercicio (clave) le estaba hablando el asistente en el mensaje anterior, y devuelve EXACTAMENTE esa misma clave.
    3. Si el usuario pide algo ajeno a la programación o que NO está en el catálogo, devuelve la palabra NINGUNO.
    
    REGLA ABSOLUTA: Tu respuesta debe ser EXCLUSIVAMENTE la clave o la palabra NINGUNO. Sin comillas, ni punto final, ni explicaciones.
    """
    
    mensajes_buscador = [SystemMessage(content=prompt_buscador)] + chat_history[-4:] + [HumanMessage(content=user_input)]
    
    # Obtenemos la ID exacta del ejercicio
    try:
        id_encontrado = llm_buscador.invoke(mensajes_buscador).content.strip()
    except Exception as e:
        print(f"Error en Nodo Demostrador (Bibliotecario): {e}")
        error_msg = "**Aviso del sistema:** Lo siento, ha ocurrido un error en el sistema. Avise a un administrador."

        return {"messages": [AIMessage(content=error_msg)]}


    
    # Instanciamos el LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0.1,
        streaming=True,
        max_tokens=3000
    )

    ejemplo_seleccionado = ejemplos.get(id_encontrado)

    if ejemplo_seleccionado:
        info_json = json.dumps(ejemplo_seleccionado, ensure_ascii=False, indent=2)
        system_prompt = f"""
        Eres el Agente Demostrador, un profesor de programación experto, paciente y muy didáctico.
        Tu objetivo es enseñar código basándote en la información proporcionada.
        
        JSON DEL EJERCICIO:
        {info_json}
        
        REGLAS DE RESPUESTA:
        1. PETICIÓN INICIAL: Si el alumno pide ver el ejemplo, muestra EXACTAMENTE el código del campo 'codigo_correcto' en Markdown. Después, utiliza el campo 'explicacion' como base teórica, pero redacta la explicación de forma didáctica, conversacional y bien formateada (usando negritas o listas si lo ves necesario para facilitar la comprensión).
        2. OFRECER VARIANTES: Tras tu explicación, enumera brevemente las variantes disponibles y anímale a elegir una (ej: "¿Qué crees que pasaría si...? Responde A para ver el error"). NO reveles el error todavía.
        3. MOSTRAR VARIANTE: Si el usuario pide una variante (ej: "Opción A"), muestra EXACTAMENTE su código ('codigo') y redacta el motivo del fallo de forma pedagógica basándote en su campo 'error'.
        4. PROHIBICIÓN: Puedes mejorar la redacción y presentación, pero NO inventes conceptos ni alteres los fragmentos de código proporcionados.
        """
    else:
        lista_temas = "\n".join([f"- {v}" for v in item_list.values()])
        system_prompt = f"""
        Eres el Agente Demostrador.
        El usuario ha pedido un ejemplo o concepto que NO tenemos en la base de datos.
        Disculpate amablemente indicando que no tienes ese ejemplo exacto, y OBLIGATORIAMENTE ofrécele elegir entre los temas de este catálogo:
        \n{lista_temas}
        """

    # El mensaje del sistema convertido en una cadena
    system_message = SystemMessage(content=system_prompt)
    
    # El mensaje del usuario
    current_message = HumanMessage(content=user_input)
    
    # Lista con todo para que el llm lo reciba
    llm_message = [system_message] + chat_history + [current_message]
    
    # Llamada directa al llm con el mensaje y el config para el streming de tokens
    try:
        respuesta = llm.invoke(llm_message, config=config)
    except Exception as e:
        print(f"Error en Nodo Demostrador: {e}")
        error_msg = "**Aviso del sistema:** Lo siento, ha ocurrido un error en el sistema. Avise a un administrador."

        return {"messages": [AIMessage(content=error_msg)]}
    
    # Devolvemos el estado actualizado
    return {"messages": [AIMessage(content=respuesta.content)]}
    
