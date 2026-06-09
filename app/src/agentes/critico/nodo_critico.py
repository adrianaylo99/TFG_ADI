import os
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from utils.funciones_auxiliares import cargar_rubrica_critico_evaluador
from utils.db_manager import obtener_categorias_errores, registrar_estadistica_error
from dotenv import load_dotenv

load_dotenv()
api_key_oss = os.getenv("GPT_OSS_KEY") 
base_url_oss = os.getenv("BASE_URL_OSS")

def nodo_critico(state, config):
    messages = state["messages"]
    user_input = messages[-1].content
    ejemplos = cargar_rubrica_critico_evaluador()

    # Extraemos las claves y los títulos para el LLM que busca errores
    catalogo_titulos = {k: v["titulo"] for k, v in ejemplos.items()}
    titulos_json = json.dumps(catalogo_titulos, ensure_ascii=False, indent=2)

    llm_detector = ChatOpenAI(
        model="gpt-oss",
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0.0,
        max_tokens=5000
    )

    prompt_detector = f"""
    Eres un analizador estático de código experto.
    Tu tarea es leer el código del alumno y comprobar si comete alguno de los errores típicos de nuestro catálogo.
    Además, debes detectar si el código tiene algún otro error que no esté en la lista.
    
    CATÁLOGO DE ERRORES:
    {titulos_json}

    REGLAS ESTRICTAS:
    1. Analiza el código y decide qué errores del catálogo se cometen.
    2. Devuelve las claves de los errores separadas por comas (ejemplo: tema4_error_1, tema2_error_3).
    3. Si encuentras un error adicional que NO está en el catálogo, añade exactamente la etiqueta '%codigo%' seguida de una breve y concisa descripción técnica de ese error al final de la respuesta.
    4. Si el código no tiene errores (o si directamente no hay código), devuelve la palabra NINGUNO.
    5. NO expliques nada. NO saludes. Solo devuelve las claves o NINGUNO.

    EJEMPLOS DE SALIDA ESPERADA:
    - tema4_error_1, tema2_error_3
    - NINGUNO %codigo% Falta cerrar la llave de la función main.
    - tema1_error_2 %codigo% Se intenta usar la variable 'x' sin haberla declarado antes.
    - NINGUNO
    """

    # Ejecutamos el detector no usamos config aquí para no mostrarlo en la interfaz por streaming
    mensajes_detector = [
        SystemMessage(content=prompt_detector), 
        HumanMessage(content=user_input)
    ]
    respuesta_detector = llm_detector.invoke(mensajes_detector).content.strip()

    # División de la respuesta
    partes = respuesta_detector.split("%codigo%")
    
    # La parte 0 siempre son las claves o la cadena NINGUNO
    texto_claves = partes[0]
    # La parte 1, si existe, es el error extra
    error_adicional = partes[1].strip() if len(partes) > 1 else ""

    # Extraemos los ejemplos a través de las claves
    claves_detectadas = [k for k in ejemplos.keys() if k in texto_claves]

    # Instanciamos el LLM
    llm = ChatOpenAI(
        model="gpt-oss",
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0.1,
        streaming=True,
    )

    if not claves_detectadas:
        # No hay errores de la rúbrica
        system_prompt = """
        Eres el Agente Crítico, un profesor experto, paciente y didáctico de Introducción a la Programación.
        El alumno te ha enviado un mensaje o un código. Tras analizarlo, NO se han encontrado errores.
        Felicítale por su buen trabajo, valida su esfuerzo de forma motivadora y anímale a seguir programando.
        Usa un tono amable y cercano.
        """
    else:
        # Se han encontrado errores
        rubrica_filtrada = {k: ejemplos[k] for k in claves_detectadas}
        info_json_filtrada = json.dumps(rubrica_filtrada, ensure_ascii=False, indent=2)

        system_prompt = f"""
        Eres el Agente Crítico, un profesor didáctico de Introducción a la Programación.
        Un alumno quiere corregir unos errores de su código y debes explicarselos.
        A continuación se te proporciona un JSON que contiene los errores que debes corregir al alumno divididos en claves del estilo "temaX_errorY".
        
        JSON DE ERRORES:
        {info_json_filtrada}
        
        REGLAS DE CORRECCIÓN:
        1. Usa la información del JSON DE ERRORES para explicarle didácticamente SOLO los errores del JSON.
        2. Pasa completamente de los errores que NO este en el JSON DE ERRORES, haz como si no estuviesen.
        3. No menciones el JSON ni el número de error en la respuesta. Responde como lo haría un profesor a su alumno.
        4. Sé amable, constructivo y formatea el código usando Markdown.
        """

    # El mensaje del sistema convertido en una cadena
    system_message = SystemMessage(content=system_prompt)
    
    # El mensaje del usuario
    current_message = HumanMessage(content=user_input)
    
    # Lista con todo para que el llm lo reciba
    llm_message = [system_message] + [current_message]
    
    # Llamada directa al llm con el mensaje y el config para el streming de tokens
    respuesta = llm.invoke(llm_message, config=config)

    # Si ha habido algún error de programación no contenido en la rúbrica de la asginatura se registra en la BD por si fuese de interés
    if error_adicional:
        # Con try-except si falla la BD o el LLM no rompe el flujo de respuesta al alumno y recibe la respuesta
        try:
            # Recuperamos las categorías que ya existen en la BD
            categorias_existentes = obtener_categorias_errores()
            categorias_texto = ", ".join(categorias_existentes) if categorias_existentes else "No hay categorias registradas todavía."
            
            llm_clasificador = ChatOpenAI(
                model="gpt-oss",
                api_key=api_key_oss,
                base_url=base_url_oss,
                temperature=0.0
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
            print(f"Error silencioso al registrar la estadística: {e}")
    
    # Devolvemos el estado actualizado
    return {"messages": [AIMessage(content=respuesta.content)]}
    