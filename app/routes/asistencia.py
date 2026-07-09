from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, date, timedelta, time
import jwt
import secrets
from cachetools import TTLCache
import pytz
from app.database import get_db
from app.models import Empleado, Asistencia

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/asistencia", tags=["Asistencia QR"])

SECRET_KEY = "tu-secret-key-muy-segura-cambiar-en-produccion"
TIMEZONE = pytz.timezone("America/Caracas")
QR_TOKEN_CACHE = TTLCache(maxsize=1000, ttl=20)

def formatear_hora(dt):
    """Formatea una hora en formato AM/PM"""
    if dt is None:
        return None
    return dt.strftime("%I:%M %p")

def generar_token_qr(empleado_id: int) -> str:
    token_data = {
        "empleado_id": empleado_id,
        "timestamp": datetime.now(TIMEZONE).timestamp(),
        "nonce": secrets.token_hex(8)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
    QR_TOKEN_CACHE[token] = empleado_id
    return token

def validar_token_qr(token: str) -> int:
    if token not in QR_TOKEN_CACHE:
        raise HTTPException(status_code=401, detail="Token QR inválido o expirado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        empleado_id = payload.get("empleado_id")
        timestamp = payload.get("timestamp")
        tiempo_transcurrido = datetime.now(TIMEZONE).timestamp() - timestamp
        if tiempo_transcurrido > 20:
            del QR_TOKEN_CACHE[token]
            raise HTTPException(status_code=401, detail="Token QR expirado")
        if empleado_id != QR_TOKEN_CACHE[token]:
            raise HTTPException(status_code=401, detail="Token QR inválido")
        return empleado_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token QR inválido")

async def obtener_asistencia_dia(db: AsyncSession, empleado_id: int, fecha_actual: date):
    result = await db.execute(
        select(Asistencia).where(
            Asistencia.empleado_id == empleado_id,
            Asistencia.fecha == fecha_actual
        )
    )
    asistencia = result.scalar_one_or_none()
    
    if not asistencia:
        asistencia = Asistencia(empleado_id=empleado_id, fecha=fecha_actual)
        db.add(asistencia)
        await db.commit()
        await db.refresh(asistencia)
    
    return asistencia

@router.post("/api/entrada")
async def registrar_entrada(token_qr: str, request: Request, db: AsyncSession = Depends(get_db)):
    empleado_id = validar_token_qr(token_qr)
    ahora = datetime.now(TIMEZONE)
    # Convertir a naive (sin zona horaria) para PostgreSQL
    ahora_naive = ahora.replace(tzinfo=None)
    fecha_actual = ahora.date()
    
    asistencia = await obtener_asistencia_dia(db, empleado_id, fecha_actual)
    if asistencia.hora_entrada:
        raise HTTPException(status_code=400, detail="Ya registraste tu entrada hoy")
    
    asistencia.hora_entrada = ahora_naive
    
    result = await db.execute(select(Empleado).where(Empleado.id == empleado_id))
    empleado = result.scalar_one_or_none()
    
    hora_esperada = datetime.combine(fecha_actual, empleado.hora_entrada_default or time(9, 0))
    # Convertir a naive para comparar
    hora_esperada_naive = hora_esperada.replace(tzinfo=None)
    
    if ahora_naive > hora_esperada_naive + timedelta(minutes=10):
        asistencia.estado_puntualidad = "Retardo"
    else:
        asistencia.estado_puntualidad = "A tiempo"
    
    await db.commit()
    return {"success": True, "mensaje": f"Entrada registrada a las {ahora.strftime('%I:%M %p')}"}

@router.post("/api/salida-almuerzo")
async def registrar_salida_almuerzo(token_qr: str, request: Request, db: AsyncSession = Depends(get_db)):
    empleado_id = validar_token_qr(token_qr)
    ahora = datetime.now(TIMEZONE)
    ahora_naive = ahora.replace(tzinfo=None)
    fecha_actual = ahora.date()
    
    asistencia = await obtener_asistencia_dia(db, empleado_id, fecha_actual)
    if not asistencia.hora_entrada:
        raise HTTPException(status_code=400, detail="Debes registrar entrada primero")
    if asistencia.salida_almuerzo:
        raise HTTPException(status_code=400, detail="Ya registraste salida a almuerzo")
    asistencia.salida_almuerzo = ahora_naive
    await db.commit()
    return {"success": True, "mensaje": f"Salida a almuerzo a las {ahora.strftime('%I:%M %p')}"}

@router.post("/api/regreso-almuerzo")
async def registrar_regreso_almuerzo(token_qr: str, request: Request, db: AsyncSession = Depends(get_db)):
    empleado_id = validar_token_qr(token_qr)
    ahora = datetime.now(TIMEZONE)
    ahora_naive = ahora.replace(tzinfo=None)
    fecha_actual = ahora.date()
    
    asistencia = await obtener_asistencia_dia(db, empleado_id, fecha_actual)
    if not asistencia.salida_almuerzo:
        raise HTTPException(status_code=400, detail="Debes registrar salida a almuerzo primero")
    if asistencia.regreso_almuerzo:
        raise HTTPException(status_code=400, detail="Ya registraste regreso de almuerzo")
    asistencia.regreso_almuerzo = ahora_naive
    await db.commit()
    return {"success": True, "mensaje": f"Regreso de almuerzo a las {ahora.strftime('%I:%M %p')}"}

@router.post("/api/salida")
async def registrar_salida(token_qr: str, request: Request, db: AsyncSession = Depends(get_db)):
    empleado_id = validar_token_qr(token_qr)
    ahora = datetime.now(TIMEZONE)
    ahora_naive = ahora.replace(tzinfo=None)
    fecha_actual = ahora.date()
    
    asistencia = await obtener_asistencia_dia(db, empleado_id, fecha_actual)
    if not asistencia.hora_entrada:
        raise HTTPException(status_code=400, detail="Debes registrar entrada primero")
    if asistencia.hora_salida:
        raise HTTPException(status_code=400, detail="Ya registraste tu salida")
    asistencia.hora_salida = ahora_naive
    await db.commit()
    return {"success": True, "mensaje": f"Salida registrada a las {ahora.strftime('%I:%M %p')}"}

@router.get("/api/reporte-semanal/{empleado_id}")
async def reporte_semanal(empleado_id: int, db: AsyncSession = Depends(get_db)):
    hoy = datetime.now(TIMEZONE).date()
    lunes = hoy - timedelta(days=hoy.weekday())
    if hoy.weekday() == 6:
        lunes = hoy - timedelta(days=7)
    sabado = lunes + timedelta(days=5)
    
    result = await db.execute(
        select(Asistencia).where(
            Asistencia.empleado_id == empleado_id,
            Asistencia.fecha >= lunes,
            Asistencia.fecha <= sabado
        ).order_by(Asistencia.fecha)
    )
    asistencias = result.scalars().all()
    
    result = await db.execute(select(Empleado).where(Empleado.id == empleado_id))
    empleado = result.scalar_one_or_none()
    
    total_retardos = 0
    total_faltas = 0
    dias_trabajados = 0
    datos_dia = []
    
    for i in range(6):
        fecha_actual = lunes + timedelta(days=i)
        nombre_dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"][i]
        asistencia = next((a for a in asistencias if a.fecha == fecha_actual), None)
        
        if asistencia and asistencia.hora_entrada:
            dias_trabajados += 1
            hora_esperada = datetime.combine(fecha_actual, empleado.hora_entrada_default or time(9, 0))
            hora_esperada_naive = hora_esperada.replace(tzinfo=None)
            if asistencia.hora_entrada > hora_esperada_naive + timedelta(minutes=10):
                total_retardos += 1
                estado = "Retardo"
            else:
                estado = "A tiempo"
        else:
            total_faltas += 1
            estado = "Falta"
        
        datos_dia.append({
            "dia": nombre_dia,
            "fecha": fecha_actual.strftime("%d/%m"),
            "estado": estado,
            "hora_entrada": formatear_hora(asistencia.hora_entrada) if asistencia else None,
            "hora_salida": formatear_hora(asistencia.hora_salida) if asistencia else None
        })
    
    bono_base = 50.0
    porcentaje_bono = 1.0
    if total_retardos > 2:
        porcentaje_bono = 0.5
    elif total_retardos > 0:
        porcentaje_bono = 0.75
    if total_faltas > 1:
        porcentaje_bono = 0
    elif total_faltas == 1:
        porcentaje_bono *= 0.5
    bono_asignado = bono_base * porcentaje_bono
    
    return {
        "empleado": empleado.nombre_completo,
        "semana": f"{lunes.strftime('%d/%m')} al {sabado.strftime('%d/%m')}",
        "dias_trabajados": dias_trabajados,
        "total_retardos": total_retardos,
        "total_faltas": total_faltas,
        "bono": {
            "base": bono_base,
            "porcentaje": porcentaje_bono,
            "asignado": round(bono_asignado, 2),
            "estado": "Completo" if porcentaje_bono == 1 else "Parcial" if porcentaje_bono > 0 else "Perdido"
        },
        "detalle_dias": datos_dia
    }

@router.get("/api/empleado/{empleado_id}")
async def obtener_empleado_api(empleado_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener datos de un empleado por ID para la app móvil"""
    result = await db.execute(select(Empleado).where(Empleado.id == empleado_id))
    empleado = result.scalar_one_or_none()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    return {
        "id": empleado.id,
        "nombre_completo": empleado.nombre_completo
    }

@router.get("/qr-empleado/{empleado_id}")
async def vista_qr_empleado(request: Request, empleado_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Empleado).where(Empleado.id == empleado_id))
    empleado = result.scalar_one_or_none()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return templates.TemplateResponse("asistencia_qr.html", {"request": request, "empleado": empleado})

@router.get("/admin/qr-generator/{empleado_id}")
async def generador_qr_admin(request: Request, empleado_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Empleado).where(Empleado.id == empleado_id))
    empleado = result.scalar_one_or_none()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return templates.TemplateResponse("qr_generator.html", {"request": request, "empleado": empleado})

@router.get("/api/generate-qr-token/{empleado_id}")
async def generate_qr_token_endpoint(empleado_id: int, db: AsyncSession = Depends(get_db)):
    token = generar_token_qr(empleado_id)
    return {"token": token, "expira_segundos": 20}

@router.get("/admin/reporte-completo")
async def reporte_completo_admin(
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """Vista para administrador: Reporte completo de todos los empleados"""
    result = await db.execute(select(Empleado).where(Empleado.activo == True))
    empleados = result.scalars().all()
    
    hoy = datetime.now(TIMEZONE).date()
    lunes = hoy - timedelta(days=hoy.weekday())
    if hoy.weekday() == 6:
        lunes = hoy - timedelta(days=7)
    sabado = lunes + timedelta(days=5)
    
    reporte_empleados = []
    
    for empleado in empleados:
        result_asistencias = await db.execute(
            select(Asistencia).where(
                Asistencia.empleado_id == empleado.id,
                Asistencia.fecha >= lunes,
                Asistencia.fecha <= sabado
            ).order_by(Asistencia.fecha)
        )
        asistencias = result_asistencias.scalars().all()
        
        total_retardos = 0
        total_faltas = 0
        dias_trabajados = 0
        registros = []
        
        for i in range(6):
            fecha_actual = lunes + timedelta(days=i)
            nombre_dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"][i]
            asistencia = next((a for a in asistencias if a.fecha == fecha_actual), None)
            
            if asistencia and asistencia.hora_entrada:
                dias_trabajados += 1
                hora_esperada = datetime.combine(fecha_actual, empleado.hora_entrada_default or time(9, 0))
                hora_esperada_naive = hora_esperada.replace(tzinfo=None)
                if asistencia.hora_entrada > hora_esperada_naive + timedelta(minutes=10):
                    total_retardos += 1
                    estado = "Retardo"
                else:
                    estado = "A tiempo"
            else:
                total_faltas += 1
                estado = "Falta"
            
            registros.append({
                "dia": nombre_dia,
                "fecha": fecha_actual.strftime("%d/%m"),
                "estado": estado,
                "hora_entrada": formatear_hora(asistencia.hora_entrada) if asistencia else None,
                "hora_salida_almuerzo": formatear_hora(asistencia.salida_almuerzo) if asistencia else None,
                "regreso_almuerzo": formatear_hora(asistencia.regreso_almuerzo) if asistencia else None,
                "hora_salida": formatear_hora(asistencia.hora_salida) if asistencia else None
            })
        
        bono_base = 50.0
        porcentaje_bono = 1.0
        if total_retardos > 2:
            porcentaje_bono = 0.5
        elif total_retardos > 0:
            porcentaje_bono = 0.75
        if total_faltas > 1:
            porcentaje_bono = 0
        elif total_faltas == 1:
            porcentaje_bono *= 0.5
        
        reporte_empleados.append({
            "id": empleado.id,
            "nombre": empleado.nombre_completo,
            "dias_trabajados": dias_trabajados,
            "retardos": total_retardos,
            "faltas": total_faltas,
            "bono_asignado": round(bono_base * porcentaje_bono, 2),
            "estado_bono": "Completo" if porcentaje_bono == 1 else "Parcial" if porcentaje_bono > 0 else "Perdido",
            "registros": registros
        })
    
    return templates.TemplateResponse("admin_reporte_asistencia.html", {
        "request": request,
        "reporte_empleados": reporte_empleados,
        "semana": f"{lunes.strftime('%d/%m/%Y')} al {sabado.strftime('%d/%m/%Y')}"
    })

@router.get("/admin/lista-qr")
async def lista_qr_admin(request: Request, db: AsyncSession = Depends(get_db)):
    """Vista para administrador: Lista de empleados con enlaces QR"""
    result = await db.execute(select(Empleado).where(Empleado.activo == True).order_by(Empleado.nombre_completo))
    empleados = result.scalars().all()
    
    base_url = str(request.base_url).rstrip('/')
    
    return templates.TemplateResponse("admin_lista_qr.html", {
        "request": request,
        "empleados": empleados,
        "base_url": base_url
    })