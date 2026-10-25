# app/sedes_utils.py
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Sede, Usuario


async def get_sede_activa(request: Request, user: Usuario, db: AsyncSession) -> Sede:
    """
    Retorna la sede con la que el usuario está trabajando ahora.
    - Superadmin: la que tenga en sesión (o la primera activa)
    - Usuario normal: siempre su sede asignada
    """
    es_super = user.es_superadmin or user.rol == "superadmin"
    
    if es_super:
        sede_id = request.session.get("sede_activa_id")
        if sede_id:
            result = await db.execute(
                select(Sede).where(Sede.id == sede_id, Sede.activa == True)
            )
            sede = result.scalar_one_or_none()
            if sede:
                return sede
        
        # Si no hay sede en sesión (o es inválida), usar la primera activa
        result = await db.execute(
            select(Sede).where(Sede.activa == True).order_by(Sede.id).limit(1)
        )
        sede = result.scalar_one_or_none()
        if not sede:
            raise HTTPException(status_code=500, detail="No hay sedes activas configuradas")
        request.session["sede_activa_id"] = sede.id
        return sede
    else:
        # Usuario normal: siempre su sede
        if not user.sede_id:
            raise HTTPException(status_code=400, detail="Usuario sin sede asignada")
        
        result = await db.execute(select(Sede).where(Sede.id == user.sede_id))
        sede = result.scalar_one_or_none()
        if not sede or not sede.activa:
            raise HTTPException(status_code=403, detail="Tu sede no está activa")
        return sede


async def get_sedes_para_selector(user: Usuario, db: AsyncSession):
    """
    Lista de sedes para el dropdown del navbar.
    - Superadmin: todas las activas
    - Usuario normal: solo la suya
    """
    es_super = user.es_superadmin or user.rol == "superadmin"
    
    if es_super:
        result = await db.execute(
            select(Sede).where(Sede.activa == True).order_by(Sede.nombre)
        )
    else:
        result = await db.execute(
            select(Sede).where(Sede.id == user.sede_id)
        )
    return result.scalars().all()


async def contexto_base(request: Request, user: Usuario, db: AsyncSession) -> dict:
    """
    Contexto estándar para pasar a TODOS los templates.
    Uso: return templates.TemplateResponse("x.html", {"request": request, **await contexto_base(request, user, db), ...})
    """
    sede_activa = await get_sede_activa(request, user, db)
    sedes = await get_sedes_para_selector(user, db)
    return {
        "user": user,
        "sede_activa": sede_activa,
        "sedes": sedes,
        "es_superadmin": user.es_superadmin or user.rol == "superadmin",
    }