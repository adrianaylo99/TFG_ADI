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

def nodo_critico(state, config):
    messages = state["messages"]
    user_input = messages[-1].content
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

    prompt_detector = f"""Eres un analizador estático de código experto.
    Tu tarea es DOBLE y debes realizarla de forma muy estricta:
    TAREA A: Buscar si el código comete errores de nuestro catálogo.
    TAREA B: Buscar si el código tiene errores de sintaxis (fuera del catálogo).

    CATÁLOGO DE ERRORES:
    {titulos_json}

    REGLAS DE FORMATO DE SALIDA:
    Debes responder SIEMPRE con una única línea de texto. NO saludes, NO expliques nada.

    Para la TAREA A:
    - Si el código comete errores del catálogo, escribe sus claves separadas por comas (ej. tema4_error_1, tema4_error_2).
    - Si NO comete errores del catálogo, escribe exactamente la palabra NINGUNO.

    Para la TAREA B:
    - Busca errores como: falta de punto y coma, llaves sin cerrar, o palabras mal escritas (ej. 'retrn' en vez de 'return').
    - Si encuentras alguno de estos errores de sintaxis, añade un espacio, luego la etiqueta '%codigo%' y una breve descripción del error.
    - EXCEPCIÓN: El código del alumno suele ser un fragmento suelto. ESTÁ PROHIBIDO marcar como error la falta de '#include', la falta de 'main()' o la falta de 'using namespace std'.
    - Si la sintaxis está perfecta, simplemente NO añadas la etiqueta '%codigo%'.

    EJEMPLOS EXACTOS DE CÓMO DEBES RESPONDER:
    tema4_error_1, tema4_error_2
    NINGUNO %codigo% Falta un punto y coma (;) al final de la instrucción.
    tema4_error_3 %codigo% La palabra clave 'return' está mal escrita como 'retrn'.
    NINGUNO
    tema4_error_1
    """

    mensajes_detector = [
        SystemMessage(content=prompt_detector), 
        HumanMessage(content=user_input)
    ]
    
    try:
        respuesta_detector = llm_detector.invoke(mensajes_detector).content.strip()
    except Exception as e:
        print(f"Error en Nodo Crítico (Bibliotecario): {e}")
        error_msg = "**Aviso del sistema:** Lo siento, ha ocurrido un error en el sistema. Avise a un administrador."

        return {"messages": [AIMessage(content=error_msg)]}

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
        model=model_name,
        api_key=api_key_oss,
        base_url=base_url_oss,
        temperature=0.1,
        streaming=True,
        max_tokens=5000
    )

    if not claves_detectadas:
        # No hay errores de la rúbrica
        system_prompt = """Eres el Agente Crítico, un profesor experto, paciente y didáctico de Introducción a la Programación.
        El alumno te ha enviado un mensaje o un fragmento de código. Tras analizarlo, NO se han encontrado errores de nuestro interés.
        Felicítale por su buen trabajo, valida su esfuerzo de forma motivadora y anímale a seguir programando.
        Tu única respuesta debe ser la felicitación.
        Usa un tono amable y cercano.
        """
    else:
        # Se han encontrado errores
        rubrica_filtrada = {k: ejemplos[k] for k in claves_detectadas}
        info_json_filtrada = json.dumps(rubrica_filtrada, ensure_ascii=False, indent=2)

        system_prompt = f"""Eres el Agente Crítico, un profesor didáctico de Introducción a la Programación.
        Un alumno quiere corregir unos errores de su código y debes explicárselos.
        A continuación se te proporciona un JSON que contiene los errores que debes corregir (con ejemplos de correcciones) al alumno divididos en claves del estilo "temaX_errorY".

        JSON DE ERRORES:
        {info_json_filtrada}

        REGLAS DE CORRECCIÓN:
        1. Usa la información del JSON DE ERRORES para explicarle didácticamente TODOS los errores que aparecen JSON apoyándote en los ejemplos que se proporcionan para que tengas algo de referencia.
        2. IGNORA completamente cualquier otro error de sintaxis que NO esté en el JSON DE ERRORES (haz como si no estuviesen).
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
    try:
        respuesta = llm.invoke(llm_message, config=config)
    except Exception as e:
        print(f"Error en Nodo Crítico: {e}")
        error_msg = "**Aviso del sistema:** Lo siento, ha ocurrido un error en el sistema. Avise a un administrador."

        return {"messages": [AIMessage(content=error_msg)]}

    # Si ha habido algún error de programación no contenido en la rúbrica de la asginatura se registra en la BD por si fuese de interés
    if error_adicional:
        # Con try-except si falla la BD o el LLM no rompe el flujo de respuesta al alumno y recibe la respuesta
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
            
            prompt_clasificador = f"""Eres un sistema de clasificación automática de errores de programación.
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
    