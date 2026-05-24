from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db:5432/precision"

    # JWT Configuration
    SECRET_KEY: str = "tu-secret-key-super-seguro-cambiar-en-produccion-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 días

    class Config:
        env_file = ".env"

settings = Settings()