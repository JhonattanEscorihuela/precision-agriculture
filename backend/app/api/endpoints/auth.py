from fastapi import APIRouter

# Instancia principal del router para rutas de autenticación
router = APIRouter()

# Ruta de prueba para verificar que el router funciona
@router.post("/login")
def login():
    return {"message": "Login endpoint is working"}

@router.post("/register")
def register():
    return {"message": "Register endpoint is working"}

@router.get("/me")
def get_me():
    return {"message": "User profile endpoint is working"}