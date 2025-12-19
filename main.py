import os
import mysql.connector
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Configuración de la conexión a MySQL usando variables de entorno de Railway
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQLHOST'),
            user=os.getenv('MYSQLUSER'),
            password=os.getenv('MYSQLPASSWORD'),
            database=os.getenv('MYSQLDATABASE'),
            port=os.getenv('MYSQLPORT')
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Modelo de datos para recibir información desde Java
class Usuario(BaseModel):
    nombre: str
    email: str

@app.get("/")
def home():
    return {"mensaje": "Servidor Python en Railway funcionando correctamente"}

@app.get("/test-db")
def test_db():
    conn = get_db_connection()
    if conn and conn.is_connected():
        conn.close()
        return {"estado": "Conexión a MySQL exitosa"}
    else:
        raise HTTPException(status_code=500, detail="No se pudo conectar a la base de datos")

@app.post("/crear-usuario")
def crear_usuario(usuario: Usuario):
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Error de base de datos")
    
    try:
        cursor = conn.cursor()
        query = "INSERT INTO usuarios (nombre, email) VALUES (%s, %s)"
        values = (usuario.nombre, usuario.email)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": f"Usuario {usuario.nombre} creado con éxito"}
    except Exception as e:
        return {"error": str(e)}