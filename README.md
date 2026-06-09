# Agente Docente Inteligente (ADI)

Repositorio del **Agente Docente Inteligente (ADI)**. Este TFG consiste en un sistema tutor multi-agente, diseñado para asistir a los estudiantes de la asignatura *Introducción a la Programación*.

A través de un enrutador semántico, el sistema clasifica la intención del estudiante y deriva la petición a uno de los cuatro agentes especialistas:
- **Agente Educador:** Resuelve dudas teóricas utilizando una arquitectura RAG (Generación Aumentada por Recuperación) fija estrictamente en los apuntes de la asignatura.
- **Agente Demostrador:** Enseña código mediante ejemplos interactivos estructurados de la teoría.
- **Agente Crítico:** Ofrece retroalimentación formativa y depuración de código usando una rúbrica de errores de la asignatura.
- **Agente Evaluador:** Puntúa el código del alumno de forma determinista basándose en una rúbrica oficial.

La arquitectura está construida con **LangChain** y **LangGraph** para la orquestación del estado, **PostgreSQL** para la memoria y persisntencia, **Streamlit** para la interfaz de usuario conversacional y **LangSmith** para la trazabilidad y métricas.

*(Nota: La primera petición que vaya al agente educador siempre provoca una gran latencia en la respuesta debido al que debe generar los embeddings de la BD vectorial en ChromaDB).*

---

## 1. Formato del fichero `.env`

Para ejecutar este proyecto, es necesario configurar las variables de entorno que permitirán la conexión con las bases de datos, los modelos de lenguaje remotos y la plataforma de telemetría (LangSmith).

Crea un archivo llamado `.env` en la raíz del directorio (puedes duplicar el archivo `.env.example`) y rellénalo con el siguiente formato:

```env
# LangSmith
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://url_de_proyecto_langsmith.com
LANGSMITH_API_KEY=clave_langsmith
LANGSMITH_PROJECT="nombre_proyecto"

# Modelo gpt-oss
GPT_OSS_KEY=clave_modelo
BASE_URL_OSS="https://url_del_modelo_hosteado.es"

# Base de datos PostgreSQL
DB_HOST=localhost    # Por defecto
DB_PORT=5432         # Por defecto
DB_USER=usuario_db
DB_PASS=clave_db
DB_NAME=nombre_db
```

---

## 2. Instalación y entorno Local (usando `uv`)

Este proyecto utiliza **`uv`**, el gestor de paquetes de Python ultrarrápido.

### Requisitos previos:
1. Tener instalado Python 3.11+.
2. Tener instalado `uv` en tu sistema.
3. Tener **Ollama** ejecutándose en segundo plano con el modelo de embeddings descargado (`nomic-embed-text`).
4. Tener un servidor de PostgreSQL instalado localmente y los datos de tu `.env` apuntando a `localhost`.

### Pasos para ejecutar:

1. **Clonar el repositorio:**
   ```bash
   git clone repositorio
   cd repositorio
   ```

2. **Crear el entorno virtual y sincronizar dependencias:**
   Ejecuta el siguiente comando. `uv` leerá automáticamente el archivo `pyproject.toml` y el `uv.lock`, creará la carpeta `.venv` e instalará las versiones exactas necesarias:
   ```bash
   uv sync
   ```

3. **Ejecutar la aplicación:**
   Puedes iniciar el servidor web de Streamlit directamente a través de `uv`:
   ```bash
   uv run streamlit run src/app.py
   ```
   *La aplicación estará disponible en tu navegador en `http://localhost:8501`.*
---

## 3. Despliegue con Docker (Recomendado)

La forma más rápida, limpia y recomendada de ejecutar el proyecto es a través de Docker. Esta opción levantará la aplicación web y una base de datos PostgreSQL aislada y preconfigurada, sin necesidad de instalar Python o gestores de bases de datos en tu máquina física.

### Requisitos previos:
- Tener instalado Docker Desktop.
- Tener tu archivo `.env` configurado en la raíz del proyecto.
- Tener **Ollama** arrancado en tu ordenador (`nomic-embed-text`).

### Instrucciones de despliegue:

1. Abre una terminal en la raíz del proyecto.
2. Ejecuta el comando de construcción y orquestación:
   ```bash
   docker compose up --build
   ```
3. **Acceder al sistema:**
   Abre tu navegador y entra a `http://localhost:8501`.

*(Nota: Si deseas explorar la base de datos PostgreSQL del contenedor usando herramientas gráficas como pgAdmin, el servidor está mapeado al puerto `5433` de tu máquina local para evitar conflictos, con las credenciales indicadas en el `docker-compose.yml`).*
