import os
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from utils.funciones_auxiliares import cargar_rubrica_critico_evaluador
from utils.db_manager import obtener_categorias_errores, registrar_estadistica_error
from dotenv import load_dotenv

load_dotenv()
model_name = os.getenv("OPENAI_MODEL_NAME")
api_key_oss = os.getenv("GPT_OSS_KEY") 
base_url_oss = os.getenv("BASE_URL_OSS")

def nodo_evaluador(state, config):
    messages = state["messages"]
    user_input = messages[-1].content
    chat_history = messages[-5:-1] if len(messages) > 1 else []
    ejemplos = cargar_rubrica_critico_evaluador()

    if not ejemplos:
        error_msg = "**Aviso del sistema:** Lo siento, el sistema no se encuentra disponible por un problema técnico en el servidor. Avise a un administrador."
        return {"messages": [AIMessage(content=error_msg)]}

    # Extraemos las claves y los títulos para el LLM que busca errores
    catalogo_titulos = {k: v["titulo"] for k, v in ejemplos.items()}
    titulos_json = json.dumps(catalogo_titulos, ensure_ascii=False, indent=2)

    llm_detector = ChatOpenAI(
        model=model_name,
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0.0,
        max_tokens=3000
    )

    prompt_detector = f"""
    Eres un analizador estático de código experto.
    Tu única tarea es comprobar si el código proporcionado por el alumno comete alguno de los errores de nuestro catálogo.
    
    INSTRUCCIONES DE BÚSQUEDA DE CÓDIGO:
    1. Analiza el último mensaje del usuario para ver si ha enviado código.
    2. Si el mensaje actual NO contiene código, revisa el historial de la conversación y analiza el ÚLTIMO bloque de código que haya enviado el alumno.
    
    CATÁLOGO DE ERRORES:
    {titulos_json}

    REGLAS ESTRICTAS DE SALIDA:
    1. Devuelve las claves de los errores separadas por comas (ejemplo: tema4_error_1, tema2_error_3).
    2. Si encuentras un error adicional que NO está en el catálogo, añade la etiqueta '%codigo%' seguida de una breve y concisa descripción técnica al final de la respuesta.
    3. Si el código analizado no tiene errores, devuelve NINGUNO.
    4. ATENCIÓN: Si tras buscar en el mensaje actual y en el historial NO encuentras ningún código para evaluar, devuelve EXACTAMENTE la palabra FALTA_CODIGO.
    5. NO expliques nada. NO saludes. Tu única salida válida es el formato estricto o la palabra FALTA_CODIGO.

    EJEMPLOS DE SALIDA ESPERADA:
    - tema4_error_1, tema2_error_3
    - NINGUNO %codigo% Falta cerrar la llave de la función main.
    - tema1_error_2 %codigo% Se intenta usar la variable 'x' sin haberla declarado antes.
    - NINGUNO
    - FALTA_CODIGO
    """
    
    historial_solo_usuario = [msg for msg in chat_history if isinstance(msg, HumanMessage)]

    # Ejecutamos el detector no usamos config aquí para no mostrarlo en la interfaz por streaming
    mensajes_detector = [SystemMessage(content=prompt_detector)] + historial_solo_usuario + [HumanMessage(content=user_input)]
    try:
        respuesta_detector = llm_detector.invoke(mensajes_detector).content.strip()
    except Exception as e:
        print(f"Error en Nodo Evaluador (Bibliotecario): {e}")
        error_msg = "**Aviso del sistema:** Lo siento, ha ocurrido un error en el sistema. Avise a un administrador."

        return {"messages": [AIMessage(content=error_msg)]}
    
    if respuesta_detector == "FALTA_CODIGO":
        return {"messages": [AIMessage(content="Por favor, envíame el código que quieres que revise o evalúe.")]}

    

    # División de la respuesta
    partes = respuesta_detector.split("%codigo%")
    
    # La parte 0 siempre son las claves o la cadena NINGUNO
    texto_claves = partes[0]
    # La parte 1 es el error extra
    error_adicional = partes[1].strip() if len(partes) > 1 else ""

    # Ejemplos a través de las claves
    claves_detectadas = [k for k in ejemplos.keys() if k in texto_claves]
    rubrica_filtrada = {k: ejemplos[k] for k in claves_detectadas}
    info_json_filtrada = json.dumps(rubrica_filtrada, ensure_ascii=False, indent=2)
    
    # Instanciamos el LLM
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0,
        streaming=True,
        max_tokens=5000
    )

    system_prompt = f"""
    Eres el Agente Evaluador, experto en corrección estricta de código.
    Tu única tarea es calcular la nota final y extraer los fragmentos de código erróneos basándote en los fallos ya detectados.
    
    A continuación, se te proporciona la RÚBRICA FILTRADA en formato JSON. 
    ATENCIÓN: Un analizador experto ya ha evaluado el código y ha determinado que el alumno ha cometido TODOS y cada uno de los errores presentes en este JSON. No debes buscar si existen o no; asume que están presentes.
    
    --- ERRORES COMETIDOS POR EL ALUMNO (RÚBRICA FILTRADA) ---
    {info_json_filtrada}
    ----------------------------------------------------------
    
    REGLAS DE EVALUACIÓN ESTRICTAS:
    1. La nota base inicial es 10.
    2. Por cada error listado en el JSON anterior, lee su campo de penalización y resta esos puntos de la nota base. La nota final no puede ser inferior a 0.
    3. NO busques fallos nuevos ni evalúes el código por tu cuenta. Cíñete exclusivamente a restar los puntos de los errores del JSON proporcionado.
    4. NO expliques el error ni le des la solución al alumno. Tu labor es únicamente redactar la calificación.
    5. Busca en el historial proporcionado el código del alumno y extrae el fragmento exacto que provoca cada error del JSON para poder mostrarlo.
    
    FORMATO DE SALIDA ESTRICTO:
    **Nota Final:** [Nota calculada]
    
    **Errores detectados:**
    - [Título del error de la rúbrica] (-X puntos): `[fragmento de código del alumno que está mal en Markdown]`
    (Si no hay errores, pon "Ninguno" en este apartado).
    """


    # El mensaje del sistema convertido en una cadena
    system_message = SystemMessage(content=system_prompt)
    
    # El mensaje del usuario
    current_message = HumanMessage(content=user_input)
    
    # Lista con todo para que el llm lo reciba
    llm_message = [system_message] + historial_solo_usuario + [current_message]
    
    # Llamada directa al llm con el mensaje y el config para el streming de tokens
    try:
        respuesta = llm.invoke(llm_message, config=config)
    except Exception as e:
        print(f"Error en Nodo Evaluador: {e}")
        error_msg = "**Aviso del sistema:** Lo siento, ha ocurrido un error en el sistema. Avise a un administrador."

        return {"messages": [AIMessage(content=error_msg)]}
    
     # Si ha habido algún error de programación no contenido en la rúbrica de la asginatura se registra en la BD por si fuese de interés
    if error_adicional:
        # Con try-except si falla la BD o el LLM no rompe el flujo de respuesta al alumno y
        # recibe la respuesta
        try:
            # Recuperamos las categorías que ya existen en la BD
            categorias_existentes = obtener_categorias_errores()
            categorias_texto = ", ".join(categorias_existentes) if categorias_existentes else "No hay categorias registradas todavía."
            
            llm_clasificador = ChatOpenAI(
                model=model_name,
                api_key=api_key_oss,
                base_url=base_url_oss,
                temperature=0.0,
                max_tokens=3000
            )
            
            prompt_clasificador = f"""
            Eres un sistema de clasificación automática de errores de programación.
            Se ha detectado el siguiente error cometido por un alumno: "{error_adicional}"
            
            Aquí tienes la lista de categorías de errores que ya tenemos registradas en la base de datos:
            [{categorias_texto}]
            
            TU TAREA:
            1. Analiza el error del alumno y decide a qué categoría pertenece.
            2. Si el error encaja perfectamente en una categoría existente, devuelve ÚNICAMENTE el nombre exacto de esa categoría.
            3. Si el error NO encaja en ninguna, inventa una categoría genérica, corta y descriptiva.
            4. Tu respuesta debe contener EXCLUSIVAMENTE el nombre de la categoría, sin comillas, ni explicaciones, ni saludos.
            """
            
            respuesta_clasificador = llm_clasificador.invoke([SystemMessage(content=prompt_clasificador)])
            categoria_final = respuesta_clasificador.content.strip()
            
            # Guardamos en la base de datos la categoría nueva o incrementamos el contador de una existente
            if categoria_final:
                registrar_estadistica_error(categoria_final)
                
        except Exception as e:
            print(f"Error al registrar: {e}")

    # Devolvemos el estado actualizado
    return {"messages": [AIMessage(content=respuesta.content)]}
    