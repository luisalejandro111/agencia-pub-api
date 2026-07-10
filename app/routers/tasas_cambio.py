# app/routers/tasas_cambio.py
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from app.database import get_db
from app.services.currency_service import CurrencyService
from app.models import Usuario, TasaCambio
from app.auth import get_current_user_from_session  # 👈 IMPORTAR

import os
SECRET_KEY = os.getenv("SECRET_KEY", "SECRET_KEY_CAMBIAR_EN_PRODUCCION")

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/tasas-cambio", tags=["Tasas de Cambio"])

@router.get("/", response_class=HTMLResponse)
async def gestion_tasas(
    request: Request,
    user: Usuario = Depends(get_current_user_from_session),  # ✅
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    service = CurrencyService(db)
    tasa_actual = await service.get_tasa()
    historial = await service.get_all_tasas(limit=20)
    
    historial_formateado = []
    for t in historial:
        if t.fecha_actualizacion:
            fecha_str = t.fecha_actualizacion.strftime("%d/%m/%Y %I:%M %p")
        else:
            fecha_str = "Fecha no disponible"
        
        historial_formateado.append({
            "id": t.id,
            "valor": float(t.valor),
            "fecha_str": fecha_str,
            "activa": False
        })
    
    if historial_formateado:
        historial_formateado[0]["activa"] = True
    
    ahora_venezuela = datetime.utcnow() - timedelta(hours=4)
    hoy_str = ahora_venezuela.strftime("%d/%m/%Y %I:%M %p")
    
    return templates.TemplateResponse("dashboard/tasas_cambio.html", {
        "request": request,
        "user": user,
        "tasa_actual": float(tasa_actual),
        "tasas": historial_formateado,
        "hoy": hoy_str
    })

@router.post("/guardar")
async def guardar_tasa(
    request: Request,
    valor: str = Form(...),
    user: Usuario = Depends(get_current_user_from_session),  # ✅
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        valor_decimal = Decimal(valor.replace(',', '.'))
        if valor_decimal <= 0:
            raise ValueError("El valor debe ser mayor a 0")
        
        service = CurrencyService(db)
        await service.set_tasa(valor_decimal, user.id)
        
        return RedirectResponse(
            url="/tasas-cambio?success=1",
            status_code=303
        )
        
    except Exception as e:
        error_msg = str(e).replace(" ", "+").replace("\n", "")
        return RedirectResponse(
            url=f"/tasas-cambio?error={error_msg[:200]}",
            status_code=303
        )

@router.get("/api/actual")
async def get_tasa_actual_api(
    user: Usuario = Depends(get_current_user_from_session),  # ✅
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return {"error": "No autorizado"}
    
    service = CurrencyService(db)
    tasa = await service.get_tasa()
    
    return {
        "tasa": float(tasa),
        "fecha": (datetime.utcnow() - timedelta(hours=4)).strftime("%d/%m/%Y %H:%M")
    }