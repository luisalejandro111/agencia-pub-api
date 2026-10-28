from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user_from_session
from app.sedes_utils import obtener_sede_id_filter, contexto_base
from app.models import (
    TransferenciaInventario,
    StockSede,
    MaterialInventario,
    Sede,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ============================================
# HELPER: obtener registro StockSede
# ============================================
async def _get_stock_sede(db: AsyncSession, sede_id: int, material_id: int):
    result = await db.execute(
        select(StockSede).where(
            StockSede.sede_id == sede_id,
            StockSede.material_id == material_id
        )
    )
    return result.scalar_one_or_none()


# ============================================
# 1. LISTAR TRANSFERENCIAS (enviadas + recibidas de mi sede)
# ============================================
@router.get("/inventario/transferencias/", response_class=HTMLResponse)
async def listar_transferencias(
    request: Request,
    user=Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    sid = await obtener_sede_id_filter(request, user, db)

    result = await db.execute(
        select(TransferenciaInventario)
        .where(
            (TransferenciaInventario.origen_sede_id == sid) |
            (TransferenciaInventario.destino_sede_id == sid)
        )
        .options(
            selectinload(TransferenciaInventario.sede_origen),
            selectinload(TransferenciaInventario.sede_destino),
            selectinload(TransferenciaInventario.material),
            selectinload(TransferenciaInventario.creado_por),
            selectinload(TransferenciaInventario.recibido_por)
        )
        .order_by(TransferenciaInventario.fecha_creacion.desc())
    )
    transferencias = result.scalars().all()

    data = []
    for t in transferencias:
        data.append({
            "id": t.id,
            "codigo": t.codigo,
            "material_nombre": t.material.nombre if t.material else "—",
            "unidad": t.material.unidad_medida if t.material else "",
            "cantidad": float(t.cantidad or 0),
            "origen_nombre": t.sede_origen.nombre if t.sede_origen else "—",
            "destino_nombre": t.sede_destino.nombre if t.sede_destino else "—",
            "estado": t.estado,
            "direccion": "enviada" if t.origen_sede_id == sid else "recibida",
            "motivo": t.motivo or "",
            "fecha_creacion": t.fecha_creacion.strftime("%d/%m/%Y %H:%M") if t.fecha_creacion else "",
            "creado_por": t.creado_por.nombre if t.creado_por else "",
            "recibido_por": t.recibido_por.nombre if t.recibido_por else None,
            "puede_recibir": (t.destino_sede_id == sid and t.estado == "en_transito"),
            "puede_cancelar": (t.origen_sede_id == sid and t.estado == "en_transito"),
        })

    en_transito = len([d for d in data if d["estado"] == "en_transito"])
    enviadas = len([d for d in data if d["direccion"] == "enviada"])
    recibidas = len([d for d in data if d["direccion"] == "recibida"])

    return templates.TemplateResponse("inventario/transferencias/lista.html", {
        "request": request,
        **await contexto_base(request, user, db),
        "user": user,
        "transferencias": data,
        "sid": sid,
        "en_transito": en_transito,
        "enviadas": enviadas,
        "recibidas": recibidas,
    })


# ============================================
# 2. FORMULARIO NUEVA TRANSFERENCIA
# ============================================
@router.get("/inventario/transferencias/nuevo", response_class=HTMLResponse)
async def formulario_transferencia(
    request: Request,
    user=Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    sid = await obtener_sede_id_filter(request, user, db)

    # Sedes destino (todas menos la mía)
    sedes_result = await db.execute(
        select(Sede).where(Sede.activa == True, Sede.id != sid).order_by(Sede.nombre)
    )
    sedes = sedes_result.scalars().all()

    # Materiales con stock disponible en MI sede
    mats_result = await db.execute(
        select(MaterialInventario, StockSede.stock_actual)
        .join(StockSede, StockSede.material_id == MaterialInventario.id)
        .where(
            StockSede.sede_id == sid,
            StockSede.stock_actual > 0,
            MaterialInventario.activo == True
        )
        .order_by(MaterialInventario.nombre)
    )
    materiales = [
        {"id": m.id, "nombre": m.nombre, "unidad": m.unidad_medida or "und", "stock": float(s or 0)}
        for m, s in mats_result.all()
    ]

    return templates.TemplateResponse("inventario/transferencias/nuevo.html", {
        "request": request,
        **await contexto_base(request, user, db),
        "user": user,
        "sedes": sedes,
        "materiales": materiales,
    })


# ============================================
# 3. CREAR TRANSFERENCIA (Opción A: descuenta stock de origen YA)
# ============================================
@router.post("/inventario/transferencias/crear")
async def crear_transferencia(
    request: Request,
    user=Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    sid = await obtener_sede_id_filter(request, user, db)
    form = await request.form()

    try:
        destino_id = int(form.get("destino_sede_id", 0) or 0)
        material_id = int(form.get("material_id", 0) or 0)
        cantidad = float(form.get("cantidad", 0) or 0)
        motivo = (form.get("motivo") or "").strip() or None

        if destino_id <= 0 or material_id <= 0 or cantidad <= 0:
            raise ValueError("Seleccione sede destino, material y una cantidad mayor a 0")

        if destino_id == sid:
            raise ValueError("La sede destino debe ser diferente a la sede origen")

        sede_dest = (await db.execute(
            select(Sede).where(Sede.id == destino_id, Sede.activa == True)
        )).scalar_one_or_none()
        if not sede_dest:
            raise ValueError("Sede destino no válida")

        material = (await db.execute(
            select(MaterialInventario).where(MaterialInventario.id == material_id)
        )).scalar_one_or_none()
        if not material:
            raise ValueError("Material no encontrado")

        # 🔥 Verificar y descontar stock de ORIGEN inmediatamente (Opción A)
        stock_origen = await _get_stock_sede(db, sid, material_id)
        stock_disp = float(stock_origen.stock_actual or 0) if stock_origen else 0.0

        if stock_disp + 1e-9 < cantidad:
            raise ValueError(f"Stock insuficiente: disponible {stock_disp} {material.unidad_medida or 'und'}")

        stock_origen.stock_actual = stock_disp - cantidad

        # Código único: TRF-2026-0001
        anio = datetime.now().year
        max_id = (await db.execute(
            select(func.coalesce(func.max(TransferenciaInventario.id), 0))
        )).scalar() or 0
        codigo = f"TRF-{anio}-{max_id + 1:04d}"

        transferencia = TransferenciaInventario(
            codigo=codigo,
            origen_sede_id=sid,
            destino_sede_id=destino_id,
            material_id=material_id,
            cantidad=cantidad,
            tallas_detalle=None,
            estado="en_transito",
            motivo=motivo,
            creado_por_id=user.id,
            fecha_envio=datetime.utcnow(),
        )
        db.add(transferencia)
        await db.commit()

        return RedirectResponse(
            url=f"/inventario/transferencias/?mensaje=Transferencia+{codigo}+creada+y+enviada",
            status_code=303
        )

    except Exception as e:
        await db.rollback()
        msg = str(e).replace(" ", "+")
        return RedirectResponse(url=f"/inventario/transferencias/nuevo?error={msg}", status_code=303)


# ============================================
# 4. RECIBIR TRANSFERENCIA (solo sede destino)
# ============================================
@router.post("/inventario/transferencias/{transferencia_id}/recibir")
async def recibir_transferencia(
    transferencia_id: int,
    request: Request,
    user=Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    sid = await obtener_sede_id_filter(request, user, db)

    try:
        t = (await db.execute(
            select(TransferenciaInventario).where(TransferenciaInventario.id == transferencia_id)
        )).scalar_one_or_none()

        if not t:
            raise ValueError("Transferencia no encontrada")
        if t.destino_sede_id != sid:
            raise ValueError("Solo la sede destino puede recibir esta transferencia")
        if t.estado != "en_transito":
            raise ValueError(f"Esta transferencia ya está {t.estado}")

        # 🔥 Sumar stock en DESTINO (crear StockSede si no existe)
        stock_dest = await _get_stock_sede(db, sid, t.material_id)
        if stock_dest:
            stock_dest.stock_actual = float(stock_dest.stock_actual or 0) + float(t.cantidad)
        else:
            material = (await db.execute(
                select(MaterialInventario).where(MaterialInventario.id == t.material_id)
            )).scalar_one_or_none()
            stock_dest = StockSede(
                sede_id=sid,
                material_id=t.material_id,
                stock_actual=float(t.cantidad),
                stock_minimo=float(material.stock_minimo or 0) if material else 0.0,
            )
            db.add(stock_dest)

        t.estado = "completada"
        t.recibido_por_id = user.id
        t.fecha_recepcion = datetime.utcnow()

        await db.commit()
        return RedirectResponse(
            url=f"/inventario/transferencias/?mensaje=Transferencia+{t.codigo}+recibida+correctamente",
            status_code=303
        )

    except Exception as e:
        await db.rollback()
        msg = str(e).replace(" ", "+")
        return RedirectResponse(url=f"/inventario/transferencias/?error={msg}", status_code=303)


# ============================================
# 5. CANCELAR TRANSFERENCIA (solo sede origen, revierte stock)
# ============================================
@router.post("/inventario/transferencias/{transferencia_id}/cancelar")
async def cancelar_transferencia(
    transferencia_id: int,
    request: Request,
    user=Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    sid = await obtener_sede_id_filter(request, user, db)

    try:
        t = (await db.execute(
            select(TransferenciaInventario).where(TransferenciaInventario.id == transferencia_id)
        )).scalar_one_or_none()

        if not t:
            raise ValueError("Transferencia no encontrada")
        if t.origen_sede_id != sid:
            raise ValueError("Solo la sede origen puede cancelar esta transferencia")
        if t.estado != "en_transito":
            raise ValueError(f"Esta transferencia ya está {t.estado}")

        # 🔥 Revertir stock en ORIGEN
        stock_origen = await _get_stock_sede(db, sid, t.material_id)
        if stock_origen:
            stock_origen.stock_actual = float(stock_origen.stock_actual or 0) + float(t.cantidad)
        else:
            db.add(StockSede(
                sede_id=sid,
                material_id=t.material_id,
                stock_actual=float(t.cantidad),
                stock_minimo=0.0,
            ))

        t.estado = "cancelada"
        await db.commit()
        return RedirectResponse(
            url=f"/inventario/transferencias/?mensaje=Transferencia+{t.codigo}+cancelada+y+stock+revertido",
            status_code=303
        )

    except Exception as e:
        await db.rollback()
        msg = str(e).replace(" ", "+")
        return RedirectResponse(url=f"/inventario/transferencias/?error={msg}", status_code=303)