"""
OE1 - CRUD operations para usuarios.
Solo operaciones de base de datos, sin lógica de negocio.
"""

from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import bcrypt

from app.models.user import User, UserCreate


def get_password_hash(password: str) -> str:
    """Genera hash bcrypt de una contraseña"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Busca un usuario por email.

    Returns:
        Usuario si existe, None si no existe
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Busca un usuario por ID.

    Returns:
        Usuario si existe, None si no existe
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Crea un nuevo usuario en la base de datos.

    Args:
        db: Sesión de base de datos
        user_data: Datos del usuario incluyendo contraseña en texto plano

    Returns:
        Usuario creado con contraseña hasheada
    """
    from datetime import datetime

    # Hashear la contraseña
    hashed_password = get_password_hash(user_data.password)

    # Crear usuario (sin password, con hashed_password)
    user_dict = user_data.dict(exclude={"password"})
    db_user = User(
        **user_dict,
        hashed_password=hashed_password,
        created_at=datetime.utcnow().isoformat() + "Z"
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user
