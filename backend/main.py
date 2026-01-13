from fastapi import FastAPI
from app.api.endpoints import polygons, auth  # Importa los routers
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db

app = FastAPI()

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(polygons.router, prefix="/polygons", tags=["Polygons"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.on_event("startup")
async def on_startup():
    # Inicializar la base de datos
    await init_db()

@app.get("/")
def read_root():
    return {"message": "Backend is running"}