import os
import mysql.connector
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Configuración de conexión compatible con Aiven (SSL)
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQLHOST'),
            user=os.getenv('MYSQLUSER'),
            password=os.getenv('MYSQLPASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            port=os.getenv('MYSQLPORT'),
            # Aiven requiere SSL. Si da error, intenta comentar esta línea
            ssl_disabled=False 
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Modelo de datos actualizado para incluir contraseña
class Usuario(BaseModel):
    nombre: Optional[str] = None
    email: str
    password: str

@app.get("/")
def home():
    return {"mensaje": "Servidor Python en Render conectado a Aiven"}

# --- RUTA PARA CREAR USUARIO ---
@app.post("/crear-usuario")
def crear_usuario(usuario: Usuario):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión a la BD")
    
    try:
        cursor = conn.cursor()
        # Actualizamos la consulta para incluir el campo 'password'
        query = "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)"
        values = (usuario.nombre, usuario.email, usuario.password)
        
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"Usuario {usuario.nombre} creado con éxito"}
    except mysql.connector.Error as e:
        # Manejo de error si el email ya existe (si pusiste UNIQUE en la BD)
        return {"error": str(e)}

# --- RUTA PARA LOGIN ---
@app.post("/login")
def login(usuario: Usuario):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de conexión")

    try:
        # Usamos dictionary=True para que el resultado sea un objeto fácil de leer
        cursor = conn.cursor(dictionary=True)
        
        # Buscamos un usuario que coincida con email Y password
        query = "SELECT id, nombre, email FROM usuarios WHERE email = %s AND password = %s"
        cursor.execute(query, (usuario.email, usuario.password))
        
        user_found = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if user_found:
            # Login exitoso
            return {
                "estado": "success",
                "mensaje": "Login exitoso",
                "usuario": user_found
            }
        else:
            # Login fallido
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- OBTENER CASAS ---
@app.get("/casas")
def get_casas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM casas")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

# --- OBTENER PRODUCTOS DE UNA CASA ---
@app.get("/productos/{casa_id}")
def get_productos(casa_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos WHERE casa_id = %s", (casa_id,))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

# --- AGREGAR PRODUCTO ---
@app.post("/productos/agregar")
def agregar_producto(prod: dict): # {nombre, casa_id}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO productos (nombre, casa_id) VALUES (%s, %s)", 
                   (prod['nombre'], prod['casa_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "ok"}