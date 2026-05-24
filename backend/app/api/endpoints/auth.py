"""
OE1 - Endpoints de autenticación de usuarios.
Solo orquestación, lógica en app/core/security.py y app/crud/user.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.user import UserCreate, UserLogin, Token, UserPublic, User
from app.crud.user import get_user_by_email, create_user
from app.core.security import verify_password, create_access_token, get_current_user

router = APIRouter()


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    Registra un nuevo usuario.

    - **email**: Email único del usuario
    - **full_name**: Nombre completo
    - **password**: Contraseña (mínimo 8 caracteres)

    Returns:
        Usuario creado sin contraseña
    """
    # Verificar que el email no exista
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Crear usuario
    new_user = await create_user(db, user_data)

    return UserPublic(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_session)
):
    """
    Inicia sesión y retorna un token JWT.

    - **email**: Email del usuario
    - **password**: Contraseña

    Returns:
        Token JWT válido por 30 días
    """
    # Buscar usuario por email
    user = await get_user_by_email(db, credentials.email)

    # Verificar que existe y contraseña es correcta
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar que esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )

    # Crear token JWT con el email como subject
    access_token = create_access_token(data={"sub": user.email})

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna el perfil del usuario autenticado.

    Requiere token JWT en header: Authorization: Bearer <token>
    """
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
