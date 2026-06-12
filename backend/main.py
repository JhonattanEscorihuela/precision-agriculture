import logging

# Configurar logger raíz
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Activar queries SQL SIN duplicados
# (funciona porque echo=False, solo hay un handler)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

from fastapi import FastAPI
from app.api.endpoints import polygons, auth, sentinel, ndvi, ndvi_batch  # Importa los routers
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db

# Importar modelos para que SQLModel los registre
from app.models.user import User
from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition
from app.models.analysis import NDVIResult  # OE2

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
app.include_router(sentinel.router, prefix="/api/sentinel", tags=["Sentinel-2"])
app.include_router(ndvi.router, prefix="/api/ndvi", tags=["NDVI"])  # OE2
app.include_router(ndvi_batch.router, prefix="/api/ndvi", tags=["NDVI Batch"])  # OE2 - Batch processing

@app.on_event("startup")
async def on_startup():
    # Inicializar la base de datos
    await init_db()

@app.get("/")
def read_root():
    return {"message": "Backend is running"}