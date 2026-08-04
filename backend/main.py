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
from app.api.endpoints import polygons, auth, sentinel, ndvi, ndvi_batch, segmentation, texture, analysis, phenology  # Importa los routers
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db

# Importar modelos para que SQLModel los registre
from app.models.user import User
from app.models.polygon import Polygon
from app.models.acquisition import SentinelAcquisition
from app.models.analysis import NDVIResult  # OE2
from app.models.segmentation import SegmentationResult  # OE3
from app.models.texture import TextureDescriptor  # OE4

app = FastAPI()

# Middleware de CORS
# ⚠️ SEGURIDAD: Lista específica de orígenes permitidos (NO "*")
# Configurado via CORS_ORIGINS en .env (separados por comas)
from app.core.config import settings as config_settings

origins = [origin.strip() for origin in config_settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(polygons.router, prefix="/polygons", tags=["Polygons"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(sentinel.router, prefix="/api/sentinel", tags=["Sentinel-2"])
app.include_router(ndvi.router, prefix="/api/ndvi", tags=["NDVI"])  # OE2
app.include_router(ndvi_batch.router, prefix="/api/ndvi", tags=["NDVI Batch"])  # OE2 - Batch processing
app.include_router(segmentation.router, prefix="/api/segmentation", tags=["Segmentation"])  # OE3
app.include_router(texture.router, prefix="/api/texture", tags=["Texture"])  # OE4
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis Pipeline"])  # OE3+OE4
app.include_router(phenology.router, prefix="/api/phenology", tags=["Phenology"])  # OE3

@app.on_event("startup")
async def on_startup():
    """
    Evento de startup: inicializa BD y valida configuración.
    """
    # Validar variables de entorno críticas
    await validate_environment()

    # Inicializar la base de datos
    await init_db()


async def validate_environment():
    """
    Valida que todas las variables de entorno críticas estén configuradas.
    Si faltan variables obligatorias, el servidor no arranca (fail-fast).
    """
    from app.core.config import settings

    required_vars = {
        "DATABASE_URL": settings.DATABASE_URL,
        "SECRET_KEY": getattr(settings, "SECRET_KEY", None),
        "SENTINEL_CLIENT_ID": settings.SENTINEL_CLIENT_ID,
        "SENTINEL_CLIENT_SECRET": settings.SENTINEL_CLIENT_SECRET,
    }

    missing = []
    for var_name, var_value in required_vars.items():
        # SECRET_KEY es obligatorio
        if var_name == "SECRET_KEY" and not var_value:
            missing.append(var_name)
        # Sentinel credentials son opcionales para tests, pero se advierte
        elif var_name.startswith("SENTINEL_") and not var_value:
            logging.warning(f"⚠️  {var_name} no configurado (opcional para tests)")

    if missing:
        error_msg = f"❌ Missing required environment variables: {missing}\n"
        error_msg += "💡 Set SECRET_KEY in backend/.env (generate with: openssl rand -hex 32)"
        logging.error(error_msg)
        raise RuntimeError(error_msg)

    logging.info("✅ Environment variables validated successfully")
    logging.info(f"   DATABASE_URL: {settings.DATABASE_URL[:30]}...")
    logging.info(f"   JWT Algorithm: {settings.ALGORITHM}")
    logging.info(f"   Token expiration: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

@app.get("/")
def read_root():
    return {"message": "Backend is running"}