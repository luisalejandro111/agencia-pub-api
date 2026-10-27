from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, literal, func
from datetime import datetime
from app.database import get_db
from app.models import Cliente, Trabajo, DeudaManual
from app.auth import get_current_user_from_session

router = APIRouter()


# ============================================
# HELPER: SEDE ACTIVA
# ============================================
def _sede_activa_id(request: Request, user) -> int:
    """Devuelve el id de sede con el que debe trabajar el usuario."""
    sid = request.session.get("sede_activa_id")
    es_super = getattr(user, "es_superadmin", False) or str(getattr(user, "rol", "") or "").lower() == "superadmin"
    if not sid or not es_super:
        sid = getattr(user, "sede_id", None)
    return int(sid or 1)


# ============================================
# CLIENTES ACTIVOS (filtrados por sede)
# ============================================
@router.get("/clientes/activos")
async def get_clientes_activos(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session)
):
    """Obtener clientes activos de la sede activa"""
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    sid = _sede_activa_id(request, user)
    try:
        result = await db.execute(
            select(Cliente).where(
                Cliente.activo == True,
                Cliente.sede_id == sid  # 🔥 FILTRO POR SEDE
            )
        )
        clientes = result.scalars().all()
        return [
            {
                "id": c.id,
                "nombre_razon_social": c.nombre_razon_social,
                "nombre": c.nombre_razon_social
            }
            for c in clientes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DEUDAS PENDIENTES (filtradas por sede)
# ============================================
@router.get("/deudas/pendientes")
async def get_deudas_pendientes(
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    origen: str = None,
    user=Depends(get_current_user_from_session)
):
    """Obtener deudas pendientes de la sede activa"""
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    sid = _sede_activa_id(request, user)
    try:
        # 1. Trabajos con saldo pendiente (0% o 50%) DE ESTA SEDE
        trabajos_query = (
            select(
                literal('trabajo').label('origen'),
                Trabajo.id.label('trabajo_id'),
                literal(None).label('deuda_manual_id'),
                Trabajo.cliente_id,
                Cliente.nombre_razon_social.label('cliente_nombre'),
                Trabajo.nombre_trabajo.label('concepto'),
                Trabajo.monto_total.label('monto_total'),
                func.coalesce(Trabajo.monto_pagado_usd, 0).label('monto_pagado'),
                (Trabajo.monto_total - func.coalesce(Trabajo.monto_pagado_usd, 0)).label('saldo_pendiente'),
                Trabajo.fecha_creacion.label('fecha'),
                Trabajo.porcentaje_pagado.label('porcentaje_pagado'),
                literal(None).label('estado_deuda')
            )
            .join(Cliente, Trabajo.cliente_id == Cliente.id)
            .where(
                Trabajo.porcentaje_pagado.in_([0, 50]),
                Trabajo.sede_id == sid  # 🔥 FILTRO POR SEDE
            )
        )

        # 2. Deudas manuales DE ESTA SEDE
        deudas_manuales_query = (
            select(
                literal('manual').label('origen'),
                literal(None).label('trabajo_id'),
                DeudaManual.id.label('deuda_manual_id'),
                DeudaManual.cliente_id,
                Cliente.nombre_razon_social.label('cliente_nombre'),
                DeudaManual.nombre_trabajo.label('concepto'),
                DeudaManual.monto_deuda.label('monto_total'),
                DeudaManual.monto_pagado.label('monto_pagado'),
                DeudaManual.saldo_pendiente.label('saldo_pendiente'),
                DeudaManual.fecha_registro.label('fecha'),
                literal(None).label('porcentaje_pagado'),
                DeudaManual.estado.label('estado_deuda')
            )
            .join(Cliente, DeudaManual.cliente_id == Cliente.id)
            .where(
                DeudaManual.estado.in_(['pendiente', 'parcial']),
                DeudaManual.sede_id == sid  # 🔥 FILTRO POR SEDE
            )
        )

        # Aplicar filtros
        if search:
            search_filter = f"%{search}%"
            trabajos_query = trabajos_query.where(Cliente.nombre_razon_social.ilike(search_filter))
            deudas_manuales_query = deudas_manuales_query.where(Cliente.nombre_razon_social.ilike(search_filter))

        if origen == 'trabajo':
            # Solo trabajos: ejecutamos trabajos y deudas vacío
            deudas_manuales_query = deudas_manuales_query.where(literal(False))
        elif origen == 'manual':
            trabajos_query = trabajos_query.where(literal(False))

        # Ejecutar ambas consultas por separado y combinar
        trabajos_result = await db.execute(
            trabajos_query.order_by('cliente_nombre', 'fecha').offset(skip).limit(limit)
        )
        deudas_result = await db.execute(
            deudas_manuales_query.order_by('cliente_nombre', 'fecha').offset(skip).limit(limit)
        )

        trabajos_rows = trabajos_result.fetchall()
        deudas_rows = deudas_result.fetchall()

        # Combinar resultados manualmente
        todos = []
        for r in trabajos_rows:
            todos.append({
                "cliente_id": r.cliente_id,
                "cliente_nombre": r.cliente_nombre,
                "concepto": r.concepto,
                "monto_total": float(r.monto_total or 0),
                "monto_pagado": float(r.monto_pagado or 0),
                "saldo_pendiente": float(r.saldo_pendiente or 0),
                "fecha": r.fecha.isoformat() if r.fecha else None,
                "origen": r.origen,
                "trabajo_id": r.trabajo_id,
                "deuda_manual_id": r.deuda_manual_id,
                "porcentaje_pagado": r.porcentaje_pagado,
                "estado_deuda": r.estado_deuda or ('pagado' if r.porcentaje_pagado == 100 else 'pendiente')
            })
        for r in deudas_rows:
            todos.append({
                "cliente_id": r.cliente_id,
                "cliente_nombre": r.cliente_nombre,
                "concepto": r.concepto,
                "monto_total": float(r.monto_total or 0),
                "monto_pagado": float(r.monto_pagado or 0),
                "saldo_pendiente": float(r.saldo_pendiente or 0),
                "fecha": r.fecha.isoformat() if r.fecha else None,
                "origen": r.origen,
                "trabajo_id": r.trabajo_id,
                "deuda_manual_id": r.deuda_manual_id,
                "porcentaje_pagado": r.porcentaje_pagado,
                "estado_deuda": r.estado_deuda or ('pagado' if r.porcentaje_pagado == 100 else 'pendiente')
            })

        # Ordenar combinados por cliente_nombre y fecha
        todos.sort(key=lambda x: (x["cliente_nombre"] or "", x["fecha"] or ""))

        # Conteos
        conteo_trab = await db.execute(
            select(func.count()).select_from(
                select(Trabajo.id)
                .join(Cliente, Trabajo.cliente_id == Cliente.id)
                .where(
                    Trabajo.porcentaje_pagado.in_([0, 50]),
                    Trabajo.sede_id == sid
                )
            )
        )
        total_trabajos = conteo_trab.scalar() or 0

        conteo_deudas = await db.execute(
            select(func.count()).select_from(
                select(DeudaManual.id)
                .join(Cliente, DeudaManual.cliente_id == Cliente.id)
                .where(
                    DeudaManual.estado.in_(['pendiente', 'parcial']),
                    DeudaManual.sede_id == sid
                )
            )
        )
        total_deudas = conteo_deudas.scalar() or 0

        return {
            "total_registros": total_trabajos + total_deudas,
            "total_clientes_unicos": len(set([d["cliente_id"] for d in todos])),
            "total_adeudado": sum([d["saldo_pendiente"] for d in todos]),
            "deudores": todos,
            "resumen_por_origen": {
                "trabajos": total_trabajos,
                "manuales": total_deudas
            }
        }

    except Exception as e:
        print(f"Error en get_deudas_pendientes: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CREAR DEUDA MANUAL (asigna sede activa)
# ============================================
@router.post("/deudas/manual/")
async def crear_deuda_manual_endpoint(
    request: Request,
    deuda_data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session)
):
    """Crear deuda manual en la sede activa"""
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    sid = _sede_activa_id(request, user)
    try:
        cliente_id = deuda_data.get("cliente_id")
        nombre_trabajo = deuda_data.get("nombre_trabajo")
        monto_deuda = deuda_data.get("monto_deuda")
        observaciones = deuda_data.get("observaciones")

        # Validar cliente
        result = await db.execute(
            select(Cliente).where(Cliente.id == cliente_id, Cliente.activo == True)
        )
        cliente = result.scalar_one_or_none()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # Crear deuda
        nueva_deuda = DeudaManual(
            cliente_id=cliente_id,
            nombre_trabajo=nombre_trabajo,
            monto_deuda=monto_deuda,
            saldo_pendiente=monto_deuda,
            monto_pagado=0.0,
            estado="pendiente",
            observaciones=observaciones,
            fecha_registro=datetime.utcnow(),
            sede_id=sid  # 🔥 ASIGNAR SEDE ACTIVA
        )

        db.add(nueva_deuda)
        await db.commit()
        await db.refresh(nueva_deuda)

        return {
            "id": nueva_deuda.id,
            "cliente_id": nueva_deuda.cliente_id,
            "nombre_trabajo": nueva_deuda.nombre_trabajo,
            "monto_deuda": float(nueva_deuda.monto_deuda),
            "saldo_pendiente": float(nueva_deuda.saldo_pendiente),
            "monto_pagado": float(nueva_deuda.monto_pagado),
            "estado": nueva_deuda.estado,
            "fecha_registro": nueva_deuda.fecha_registro.isoformat(),
            "observaciones": nueva_deuda.observaciones,
            "es_convertida_a_trabajo": False,
            "trabajo_convertido_id": None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PAGAR DEUDA MANUAL (solo deudas de la sede)
# ============================================
@router.put("/deudas/manual/{deuda_id}/pagar/")
async def pagar_deuda_manual(
    request: Request,
    deuda_id: int,
    pago_data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_from_session)
):
    """Registrar pago de deuda manual (solo deudas de la sede activa)"""
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    sid = _sede_activa_id(request, user)
    try:
        monto_pago = pago_data.get("monto_pago")

        if not monto_pago or monto_pago <= 0:
            raise HTTPException(status_code=400, detail="Monto de pago inválido")

        # 🔥 Solo deudas de esta sede
        result = await db.execute(
            select(DeudaManual).where(
                DeudaManual.id == deuda_id,
                DeudaManual.sede_id == sid
            )
        )
        deuda = result.scalar_one_or_none()
        if not deuda:
            raise HTTPException(status_code=404, detail="Deuda no encontrada")

        if deuda.estado == 'pagado':
            raise HTTPException(status_code=400, detail="Deuda ya pagada")

        if float(monto_pago) > float(deuda.saldo_pendiente):
            raise HTTPException(status_code=400, detail="Monto excede el saldo pendiente")

        deuda.monto_pagado = float(deuda.monto_pagado) + float(monto_pago)
        deuda.saldo_pendiente = float(deuda.saldo_pendiente) - float(monto_pago)

        if float(deuda.saldo_pendiente) <= 0:
            deuda.estado = 'pagado'
        elif float(deuda.monto_pagado) > 0:
            deuda.estado = 'parcial'

        deuda.fecha_actualizacion = datetime.utcnow()

        await db.commit()
        await db.refresh(deuda)

        return {
            "id": deuda.id,
            "cliente_id": deuda.cliente_id,
            "nombre_trabajo": deuda.nombre_trabajo,
            "monto_deuda": float(deuda.monto_deuda),
            "saldo_pendiente": float(deuda.saldo_pendiente),
            "monto_pagado": float(deuda.monto_pagado),
            "estado": deuda.estado,
            "fecha_registro": deuda.fecha_registro.isoformat(),
            "observaciones": deuda.observaciones,
            "es_convertida_a_trabajo": False,
            "trabajo_convertido_id": None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))