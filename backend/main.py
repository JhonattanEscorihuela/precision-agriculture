from fastapi import FastAPI
from app.api.endpoints import polygons, auth  # Importamos los routers
from fastapi.middleware.cors import CORSMiddleware  # CORS middleware

# Instancia principal de FastAPI
app = FastAPI(title="Agricultura de Precisión", version="1.0")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las fuentes durante desarrollo
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers para las rutas
app.include_router(polygons.router, prefix="/polygons", tags=["Polygons"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Punto de inicio básico para verificar que funciona
@app.get("/")
def read_root():
    return {"message": "Backend is running"}