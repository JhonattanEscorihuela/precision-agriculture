from pydantic import BaseSettings

class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación.
    Todas las variables se leen desde .env (NUNCA hardcodeadas).
    """
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db:5432/precision"

    # JWT Configuration
    # ⚠️ CRÍTICO: SECRET_KEY debe estar en .env, NO tiene default por seguridad
    # Generar con: openssl rand -hex 32
    SECRET_KEY: str  # Sin default value - OBLIGATORIO en .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 días

    # Sentinel-2 / Copernicus DataSpace Credentials
    SENTINEL_CLIENT_ID: str = ""  # Opcional: tiene default vacío para tests
    SENTINEL_CLIENT_SECRET: str = ""  # Opcional: tiene default vacío para tests

    class Config:
        env_file = ".env"

settings = Settings()