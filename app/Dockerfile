# Imagen oficial y ligera de Python
FROM python:3.11-slim

# Instalamos uv
RUN pip install uv

# El directorio de trabajo dentro del contenedor
WORKDIR /app

COPY pyproject.toml uv.lock ./

# Instalamos las dependencias usando uv
RUN uv sync --frozen --no-install-project

# Todo el resto de ficheros
COPY . .

# Abrimos el puerto de Streamlit
EXPOSE 8501

# Comando para arrancar la app usando uv
CMD ["uv", "run", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]