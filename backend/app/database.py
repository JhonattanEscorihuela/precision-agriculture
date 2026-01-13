from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

# Motor de la base de datos
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Crear una sesión para interactuar con la base de datos
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Crear tablas si no existen
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependencia para obtener la sesión
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session