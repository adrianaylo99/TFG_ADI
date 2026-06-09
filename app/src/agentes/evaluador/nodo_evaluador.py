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

def nodo_evaluador(state, config):
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
    # La parte 1 es el error extra
    error_adicional = partes[1].strip() if len(partes) > 1 else ""

    # Ejemplos a través de las claves
    claves_detectadas = [k for k in ejemplos.keys() if k in texto_claves]
    rubrica_filtrada = {k: ejemplos[k] for k in claves_detectadas}
    info_json_filtrada = json.dumps(rubrica_filtrada, ensure_ascii=False, indent=2)
    
    # Instanciamos el LLM
    llm = ChatOpenAI(
        model="gpt-oss",
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0,
        streaming=True
    )

    system_prompt = f"""
    Eres el Agente Evaluador, experto en corrección estricta de código.
    Tu única tarea es puntuar el código proporcionado por el alumno basándote en una rúbrica.
    Si el alumno no ha mandado un código con su mensaje, pídele amablemente que te lo proporcione en otro mensaje para poder evaluarlo.
    
    A continuación, se te proporciona la RÚBRICA DE EVALUACIÓN en formato JSON. 
    Esta rúbrica contiene un catálogo de errores, la explicación del fallo y los puntos que restan:
    
    --- RÚBRICA ---
    {info_json_filtrada}
    ---------------
    
    REGLAS DE EVALUACIÓN ESTRICTAS:
    1. La nota base inicial es 10.
    2. Analiza el código del alumno en busca de CUALQUIERA de los errores listados en la RÚBRICA. Ten en cuenta que un alumno puede cometer varios errores simultáneamente.
    3. Partiendo de la nota inicial, para cada error que cometa, lee su campo "penalizacion" para descubrir los puntos que penaliza y réstalos de la nota. La nota no puede ser inferior a 0.
    4. Si el código tiene fallos que NO están listados en la rúbrica, no restes puntos por ellos. Pasa de ellos.
    5. NO expliques el error ni le des la solución al alumno. Tu labor es únicamente calificar.
    
    FORMATO DE SALIDA ESTRICTO:
    **Nota Final:** [Nota]
    
    **Errores detectados:**
    - [Título del error de la rúbrica] (-X puntos): `[fragmento de código del alumno que está mal en Markdown]`
    (Si no hay errores, pon "Ninguno" en este apartado).
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
        # Con try-except si falla la BD o el LLM no rompe el flujo de respuesta al alumno y
        # recibe la respuesta
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
            print(f"Error al registrar: {e}")

    # Devolvemos el estado actualizado
    return {"messages": [AIMessage(content=respuesta.content)]}
    