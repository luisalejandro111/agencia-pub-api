# app/dependencies.py
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Usuario
from itsdangerous import URLSafeSerializer
from sqlalchemy import select

# Clave secreta - DEBE SER LA MISMA QUE USAS EN main.py
SECRET_KEY = "annie"  # ← Cambia esto por tu clave real

async def get_current_user_from_session(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el usuario actual desde la sesión
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    
    s = URLSafeSerializer(SECRET_KEY, salt="session")
    try:
        email = s.loads(session_id)
        result = await db.execute(
            select(Usuario).where(Usuario.email == email)
        )
        return result.scalar_one_or_none()
    except Exception:
        return None