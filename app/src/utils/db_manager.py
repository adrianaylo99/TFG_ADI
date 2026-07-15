import os
import uuid
import bcrypt
from dotenv import load_dotenv
from datetime import datetime
from psycopg_pool import ConnectionPool

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# URI de conexión con la base de datos
DB_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Creamos la piscina de conexiones
# Autocommit es necesario en LangGraph para que guarde los mensajes en tiempo real
pool = ConnectionPool(
    conninfo=DB_URI,
    max_size=5,
    kwargs={
        "autocommit": True
    } 
)

# Para crear las tablas necesarias si no existen
def inicializar_base_datos():
    # Con el with solo se cierra la conexión al terminar
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES usuarios(id),
                    thread_id VARCHAR(255) UNIQUE NOT NULL,
                    titulo TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    historial TEXT DEFAULT '' 
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS estadisticas_errores (
                    categoria VARCHAR(255) PRIMARY KEY,
                    contador INTEGER DEFAULT 1
                )
            ''')
        conn.commit()

try:
    inicializar_base_datos()
except Exception as e:
    print(f"No se ha podido inicializar la BD al arrancar: {e}")

# Inicio de sesión
def iniciar_sesion_usuario(username: str, password_plain: str) -> str:
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, password_hash FROM usuarios WHERE username = %s', (username,))
            row = cursor.fetchone()

            if row:
                user_id = str(row[0])
                stored_hash = row[1]
                
                if bcrypt.checkpw(password_plain.encode('utf-8'), stored_hash.encode('utf-8')):
                    return user_id
                else:
                    raise ValueError("Contraseña incorrecta.")
            else:
                raise ValueError("Usuario no registrado.")

# Registro de usuarios
def registrar_usuario(username: str, password_plain: str) -> str:
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM usuarios WHERE username = %s', (username,))
            if cursor.fetchone():
                raise ValueError("Usuario ya registrado.")
            
            hashed_bytes = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt())
            hashed_str = hashed_bytes.decode('utf-8')
            
            cursor.execute(
                'INSERT INTO usuarios (username, password_hash) VALUES (%s, %s) RETURNING id', 
                (username, hashed_str)
            )
            nuevo_id = cursor.fetchone()[0]
            conn.commit()
            return str(nuevo_id)

# Crea un nuevo hilo en la bd y devuelve el thread_id
def crear_nuevo_chat(user_id: str, titulo: str = "Nueva conversación") -> str:
    thread_id = str(uuid.uuid4())
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO chats (user_id, thread_id, titulo) VALUES (%s, %s, %s)', (user_id, thread_id, titulo))
        conn.commit()
    return thread_id

# Devuelve la lista de chats de un usuario ordenados por el más reciente
def obtener_chats_usuario(user_id: str) -> list:
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT thread_id, titulo FROM chats WHERE user_id = %s ORDER BY id DESC', (user_id,))
            return [{"thread_id": row[0], "titulo": row[1]} for row in cursor.fetchall()]

# Actualiza el título de un chat en la bd
def actualizar_titulo_chat(thread_id: str, nuevo_titulo: str):
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE chats SET titulo = %s WHERE thread_id = %s', (nuevo_titulo, thread_id))
        conn.commit()

# Devuelve una lista con los nombres de las categorías ya registradas
def obtener_categorias_errores() -> list:
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT categoria FROM estadisticas_errores')
            return [row[0] for row in cursor.fetchall()]

# Inserta una nueva categoría o incrementa su contador si ya existe
def registrar_estadistica_error(categoria: str):
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            # PostgreSQL tiene el ON CONFLICT, esto hace que si se intenta insertar una categoria
            # que ya está en la tabla, en lugar de duplicarla o no hacer nada, le incrementa el contador
            # Así si existe ese error en la tabla, le suma el contador y si no lo crea con contador a 1
            cursor.execute('''
                INSERT INTO estadisticas_errores (categoria, contador) 
                VALUES (%s, 1) 
                ON CONFLICT (categoria) 
                DO UPDATE SET contador = estadisticas_errores.contador + 1
            ''', (categoria,))

# Añade un mensaje en texto plano al historial de un chat
def agregar_mensaje_texto_plano(thread_id: str, rol: str, contenido: str):
    # Obtenemos la hora actual del servidor
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Formateamos el mensaje para que sea legible
    nuevo_bloque = f"[{rol.upper()} - {hora_actual}]: {contenido}\n\n{'#'*50}\n\n"
    
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            # El || concatena texto
            cursor.execute('''
                UPDATE chats 
                SET historial = historial || %s 
                WHERE thread_id = %s
            ''', (nuevo_bloque, thread_id))

def obtener_chat_vacio_usuario(user_id: str):
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT thread_id FROM chats WHERE user_id = %s AND historial = '' LIMIT 1", (user_id,))
            row = cursor.fetchone()
            if row:
                return str(row[0])
            return None