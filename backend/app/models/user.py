"""
OE1 - Modelo de usuarios para autenticación.
Almacena credenciales y datos básicos del usuario.
"""

from sqlmodel import SQLModel, Field
from typing import Optional


class UserBase(SQLModel):
    """Campos base para usuario"""
    email: str = Field(unique=True, index=True, description="Email único del usuario")
    full_name: str = Field(description="Nombre completo del usuario")


class User(UserBase, table=True):
    """
    Tabla de usuarios del sistema.
    Cada usuario puede tener múltiples parcelas.
    """
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(description="Contraseña hasheada con bcrypt")
    is_active: bool = Field(default=True, description="Usuario activo o bloqueado")
    created_at: str = Field(description="Timestamp de creación (ISO 8601)")

    class Config:
        """Configuración del modelo"""
        json_schema_extra = {
            "example": {
                "email": "usuario@example.com",
                "full_name": "Juan Pérez",
                "is_active": True,
                "created_at": "2026-05-23T10:30:00Z"
            }
        }


class UserCreate(UserBase):
    """Schema para crear un nuevo usuario"""
    password: str = Field(min_length=8, description="Contraseña en texto plano (mínimo 8 caracteres)")


class UserPublic(UserBase):
    """Schema público para respuestas de API (sin contraseña)"""
    id: int
    is_active: bool
    created_at: str


class UserLogin(SQLModel):
    """Schema para login"""
    email: str
    password: str


class Token(SQLModel):
    """Schema de respuesta de login"""
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
