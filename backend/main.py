from fastapi import FastAPI

# Instancia principal de FastAPI
app = FastAPI()

# Endpoint básico para verificar que el backend funciona correctamente
@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running!"}