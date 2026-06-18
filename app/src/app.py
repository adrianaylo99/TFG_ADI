import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_core.callbacks import BaseCallbackHandler
import controlador

# Para poder streaming del LLM
# Manejador de eventos para LangChain que hereda de BaseCallbackHandler
# Intercepta los tokens generados por el LLM en tiempo real y los dibuja en la 
# pantalla de Streamlit para crear un efecto de máquina de escribir
# Esto reduce el tiempo hasta el primer token y mejora la interfaz para el usuario
class StreamHandler(BaseCallbackHandler):
    def __init__(self, placeholder, status_placeholder, status_msg="*Razonando la respuesta...*"):
        self.placeholder = placeholder                  # Variable donde se guarda la respuesta final
        self.status_placeholder = status_placeholder    # Variable temporal para mostrar algo mientras el sistema piensa
        self.text = ""                                  # Variable para ir acumulando los tokens de salida
        self.first_token_received = False
        self.status_placeholder.markdown(status_msg)

    # Esta función salta cada vez que el modelo genera una nueva letra/palabra
    # Es necesario el kwargs por si LangChain introduce informacióne extra que no salte error
    # y como no los vamos a utilizar no nos interesa
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if not self.first_token_received:
            # Se borra el mensaje de pensando porque tenemos el primer token
            self.status_placeholder.empty()
            self.first_token_received = True
        
        # Acumulamos el token e imprimimos el simbolo al final para que pareza que escribe
        self.text += token
        self.placeholder.markdown(self.text + "|")

# Título de la página
st.set_page_config(page_title="Agente Docente Inteligente (ADI)", layout="centered")

# Funciones auxiliares de la interfaz
# Cambiamos el hilo del chat cuando se hace click en otro chat en la interfaz
def evt_cambiar_chat(thread_id):
    st.session_state.current_thread_id = thread_id
    st.session_state.agente_actual = "Docente Inteligente"

# Para cuando se hace click en crear el chat y se le pide al controlador
def evt_crear_chat():
    try:
        st.session_state.current_thread_id = controlador.crear_chat(st.session_state.user_id)
    except Exception as e:
        print(f"Error al crear chat en la UI: {e}")
        st.toast("No se pudo crear el chat. Problemas de conexión con el servidor.")

# Se limipian las variables de estado de sesión al cerrar sesión y se vuelve al login
def evt_cerrar_sesion():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = ""
    st.session_state.current_thread_id = ""

# Como al iniciar no tenemos logged_in iniciamos en el login con las variables limpias
if "logged_in" not in st.session_state:
    evt_cerrar_sesion()

# Pantalla de login
if not st.session_state.logged_in:
    st.title("Inicio de Sesión - ADI")
    st.markdown("Bienvenido al Agente Docente Inteligente. Por favor, identifícate.")
    
    # Formulario sencillo
    username_input = st.text_input("Nombre de usuario:", placeholder="Ej: Adrian")
    
    if st.button("Entrar al Chat"):
        # Si tenemos una cadena vacía después de hacer strip() no es un nombre válido
        nombre = username_input.strip()
        if nombre:
            try:
                st.session_state.username = nombre
                st.session_state.user_id = controlador.login_usuario(nombre)

                chats_existentes = controlador.obtener_chats(st.session_state.user_id)
                if not chats_existentes:
                    st.session_state.current_thread_id = controlador.crear_chat(st.session_state.user_id)
                else:
                    # Cargamos el chat más reciente
                    st.session_state.current_thread_id = chats_existentes[0]["thread_id"]

                st.session_state.logged_in = True
                st.rerun() # Recarga la página para ir al chat
            except Exception as e:
                print(f"Error crítico en BD al iniciar sesión: {e}")
                st.error("Error de conexión con el servidor. Inténtalo de nuevo más tarde.")
        else:
            st.warning("Por favor, introduce un nombre válido.")

# Pantalla principal del chat
else:
    # Cabecera
    if "agente_actual" not in st.session_state:
        st.session_state.agente_actual = "Docente Inteligente"
        
    st.title(body=f"Agente {st.session_state.agente_actual} - ADI", text_alignment="center")

    chats = controlador.obtener_chats(st.session_state.user_id)

    with st.sidebar:
        st.write(f"Usuario: **{st.session_state.username}**")
        
        # Al usar on_click=evt_crear_chat, ejecuta esa función en segundo plano 
        # y luego recarga la interfaz automáticamente
        st.button("Nuevo Chat", on_click=evt_crear_chat, use_container_width=True)
            
        st.divider()
        st.write("**Tus conversaciones:**")
        
        # Pintamos la lista de chats como botones
        for chat in chats:
            # Para que streamlit diferencie los botones y los pinte de forma diferente si es el principal o no
            tipo_boton = "primary" if chat["thread_id"] == st.session_state.current_thread_id else "secondary"
            st.button(
                label=chat["titulo"], 
                key=chat["thread_id"], 
                type=tipo_boton, 
                use_container_width=True,
                on_click=evt_cambiar_chat,      # Si hacemos click en el botón cambiamos de chat
                args=(chat["thread_id"],)       # Parámetro que se le pasa a la función de cambiar chat
            )
                
        st.divider()
        st.button("Cerrar sesión", on_click=evt_cerrar_sesion, use_container_width=True)

    mensajes_guardados = controlador.obtener_historial_chat(st.session_state.current_thread_id, st.session_state.username)

    if not mensajes_guardados:
        st.info("Nuevo Chat. Pregunta sobre Introducción a la Programación.")
    else:
        for msg in mensajes_guardados:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            with st.chat_message(role):
                st.markdown(msg.content)

    # Caja de texto para nuevas preguntas
    if prompt := st.chat_input(placeholder="Escribe tu pregunta sobre la teoría de IP..."):
        # Pedimos al controlador que actualice el título si es necesario
        controlador.renombrar_chat_si_aplica(st.session_state.current_thread_id, prompt, chats)

        # Si el usuario escribe algo se imprime inmediatamente con el icono preguardado para
        # el tipo "user"
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Creamos 2 huecos vacíos para mostrar algo mientras llega el primer token
            status_box = st.empty()     # El mensaje que se borra para engañar al usuario como que está pensando el modelo
            response_box = st.empty()   # El de la respuesta final
            
            # Iniciamos el Handler pasándole ambos huecos
            stream_handler = StreamHandler(
                placeholder=response_box, 
                status_placeholder=status_box,
                status_msg="*Razonando la respuesta...*"
            )
            
            # El controlador se encarga de procesar la consulta
            texto_final, agente_usado = controlador.procesar_mensaje(
                prompt=prompt,
                thread_id=st.session_state.current_thread_id,
                username=st.session_state.username,
                stream_handler=stream_handler
            )
            st.session_state.agente_actual = agente_usado

            status_box.empty()                      # Borramos el mensaje de pensando
            response_box.markdown(texto_final)      # Añadimos la respuesta final

            # Refresca la barra lateral al terminal completamente para actualizar los títulos
            # de los chats en la barra lateral
            st.rerun()