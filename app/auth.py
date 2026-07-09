# app/auth.py - VERSIÓN COMPLETA CON SESIÓN Y SOPORTE PARA USERNAME/EMAIL
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from fastapi import Request, Depends
from itsdangerous import URLSafeSerializer
from app.models import Usuario
from app.database import get_db

# Usar sha256_crypt en lugar de bcrypt
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# 🔥 CLAVE SECRETA PARA LA SESIÓN - DEBE SER LA MISMA QUE EN main.py
SECRET_KEY = "SECRET_KEY_CAMBIAR_EN_PRODUCCION"
SALT = "session"

def hash_password(password: str) -> str:
    """Genera hash de una contraseña"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_user(db: AsyncSession, username_or_email: str, password: str):
    """
    Autentica un usuario por username o email
    
    Args:
        db: Sesión de base de datos
        username_or_email: Username o Email del usuario
        password: Contraseña en texto plano
    
    Returns:
        Usuario si está autenticado, None en caso contrario
    """
    # Buscar por username o email
    result = await db.execute(
        select(Usuario).where(
            or_(
                Usuario.username == username_or_email,
                Usuario.email == username_or_email
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"❌ Usuario no encontrado: {username_or_email}")
        return None
    
    if not verify_password(password, user.hashed_password):
        print(f"❌ Contraseña incorrecta para: {username_or_email}")
        return None
    
    if not user.activo:
        print(f"❌ Usuario inactivo: {username_or_email}")
        return None
    
    print(f"✅ Usuario autenticado: {user.nombre} (Username: {user.username})")
    return user

async def authenticate_user_by_username(db: AsyncSession, username: str, password: str):
    """
    Autentica un usuario por username (legacy)
    
    Args:
        db: Sesión de base de datos
        username: Username del usuario
        password: Contraseña en texto plano
    
    Returns:
        Usuario si está autenticado, None en caso contrario
    """
    result = await db.execute(
        select(Usuario).where(Usuario.username == username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"❌ Usuario no encontrado: {username}")
        return None
    
    if not verify_password(password, user.hashed_password):
        print(f"❌ Contraseña incorrecta para: {username}")
        return None
    
    if not user.activo:
        print(f"❌ Usuario inactivo: {username}")
        return None
    
    print(f"✅ Usuario autenticado: {user.nombre}")
    return user

async def authenticate_user_by_email(db: AsyncSession, email: str, password: str):
    """
    Autentica un usuario por email (legacy)
    
    Args:
        db: Sesión de base de datos
        email: Email del usuario
        password: Contraseña en texto plano
    
    Returns:
        Usuario si está autenticado, None en caso contrario
    """
    result = await db.execute(
        select(Usuario).where(Usuario.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"❌ Usuario no encontrado: {email}")
        return None
    
    if not verify_password(password, user.hashed_password):
        print(f"❌ Contraseña incorrecta para: {email}")
        return None
    
    if not user.activo:
        print(f"❌ Usuario inactivo: {email}")
        return None
    
    print(f"✅ Usuario autenticado: {user.nombre}")
    return user

# 🔥 FUNCIÓN ACTUALIZADA: Obtener usuario desde la sesión
async def get_current_user_from_session(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el usuario actual desde la cookie de sesión
    
    Args:
        request: Request de FastAPI
        db: Sesión de base de datos
    
    Returns:
        Usuario si la sesión es válida, None en caso contrario
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        print("❌ No hay cookie de sesión")
        return None
    
    s = URLSafeSerializer(SECRET_KEY, salt=SALT)
    try:
        # Decodificar sesión (puede ser username o email)
        identifier = s.loads(session_id)
        print(f"🔍 Identificador desde sesión: {identifier}")
        
        # Buscar por username o email
        result = await db.execute(
            select(Usuario).where(
                or_(
                    Usuario.username == identifier,
                    Usuario.email == identifier
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ Usuario encontrado: {user.nombre} (Username: {user.username})")
        else:
            print(f"❌ Usuario no encontrado para: {identifier}")
        
        return user
    except Exception as e:
        print(f"❌ Error al decodificar sesión: {e}")
        return None

# 🔥 FUNCIÓN AUXILIAR: Crear sesión para un usuario
def create_session_for_user(user: Usuario) -> str:
    """
    Crea un ID de sesión para un usuario
    
    Args:
        user: Usuario autenticado
    
    Returns:
        String con el ID de sesión encriptado
    """
    s = URLSafeSerializer(SECRET_KEY, salt=SALT)
    # Usar username como identificador (siempre existe)
    return s.dumps(user.username)

# 🔥 FUNCIÓN AUXILIAR: Verificar si un usuario está autenticado
async def require_auth(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Dependency para verificar autenticación
    
    Args:
        request: Request de FastAPI
        db: Sesión de base de datos
    
    Returns:
        Usuario autenticado
    
    Raises:
        HTTPException: Si no está autenticado
    """
    from fastapi import HTTPException, status
    
    user = await get_current_user_from_session(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# 🔥 FUNCIÓN AUXILIAR: Verificar si es administrador
async def require_admin(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Dependency para verificar que el usuario sea administrador
    
    Args:
        request: Request de FastAPI
        db: Sesión de base de datos
    
    Returns:
        Usuario autenticado si es administrador
    
    Raises:
        HTTPException: Si no está autenticado o no es administrador
    """
    from fastapi import HTTPException, status
    
    user = await require_auth(request, db)
    if user.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador"
        )
    return user

# 🔥 FUNCIÓN AUXILIAR: Buscar usuario por username o email
async def find_user_by_username_or_email(db: AsyncSession, identifier: str):
    """
    Busca un usuario por username o email
    
    Args:
        db: Sesión de base de datos
        identifier: Username o Email a buscar
    
    Returns:
        Usuario si se encuentra, None en caso contrario
    """
    result = await db.execute(
        select(Usuario).where(
            or_(
                Usuario.username == identifier,
                Usuario.email == identifier
            )
        )
    )
    return result.scalar_one_or_none()

# 🔥 FUNCIÓN AUXILIAR: Verificar si username existe
async def username_exists(db: AsyncSession, username: str) -> bool:
    """
    Verifica si un username ya existe
    
    Args:
        db: Sesión de base de datos
        username: Username a verificar
    
    Returns:
        True si existe, False en caso contrario
    """
    result = await db.execute(
        select(Usuario).where(Usuario.username == username)
    )
    return result.scalar_one_or_none() is not None

# 🔥 FUNCIÓN AUXILIAR: Verificar si email existe
async def email_exists(db: AsyncSession, email: str) -> bool:
    """
    Verifica si un email ya existe
    
    Args:
        db: Sesión de base de datos
        email: Email a verificar
    
    Returns:
        True si existe, False en caso contrario
    """
    if not email:
        return False
    result = await db.execute(
        select(Usuario).where(Usuario.email == email)
    )
    return result.scalar_one_or_none() is not None
