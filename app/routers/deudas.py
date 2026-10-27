# app/routers/deudas.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, literal, and_, or_
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from fastapi import Request, Depends
from app.auth import get_current_user_from_session  # mismo módulo que usa main.py
from app.database import get_db
from app.models import Cliente, Trabajo, DeudaManual

router = APIRouter(prefix="/deudas", tags=["Cuentas por Cobrar"])




# ============================================
# HELPER: SEDE ACTIVA (sync, sin tocar BD)
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
    db: Session = Depends(get_db),
    user=Depends(get_current_user_from_session)
):
    """Obtener clientes activos de la sede activa"""
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    sid = _sede_activa_id(request, user)
    try:
        clientes = db.query(Cliente).filter(
            Cliente.activo == True,
            Cliente.sede_id == sid  # 🔥 FILTRO POR SEDE
        ).all()
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
    db: Session = Depends(get_db),
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
        from sqlalchemy import literal, func
        
        # 1. Trabajos con saldo pendiente (0% o 50%) DE ESTA SEDE
        trabajos_query = db.query(
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
        ).join(Cliente, Trabajo.cliente_id == Cliente.id).filter(
            Trabajo.porcentaje_pagado.in_([0, 50]),
            Trabajo.sede_id == sid  # 🔥 FILTRO POR SEDE
        )
        
        # 2. Deudas manuales DE ESTA SEDE
        deudas_manuales_query = db.query(
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
        ).join(Cliente, DeudaManual.cliente_id == Cliente.id).filter(
            DeudaManual.estado.in_(['pendiente', 'parcial']),
            DeudaManual.sede_id == sid  # 🔥 FILTRO POR SEDE
        )
        
        # Aplicar filtros
        if search:
            search_filter = f"%{search}%"
            trabajos_query = trabajos_query.filter(
                Cliente.nombre_razon_social.ilike(search_filter)
            )
            deudas_manuales_query = deudas_manuales_query.filter(
                Cliente.nombre_razon_social.ilike(search_filter)
            )
        
        if origen == 'trabajo':
            deudas_manuales_query = deudas_manuales_query.filter(False)
        elif origen == 'manual':
            trabajos_query = trabajos_query.filter(False)
        
        # Unir y ordenar
        resultados = trabajos_query.union_all(deudas_manuales_query).order_by(
            'cliente_nombre', 'fecha'
        ).offset(skip).limit(limit).all()
        
        # Formatear respuesta
        deudores = []
        for r in resultados:
            deudores.append({
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
        
        # Estadísticas
        total_trabajos = trabajos_query.count()
        total_deudas = deudas_manuales_query.count()
        
        return {
            "total_registros": total_trabajos + total_deudas,
            "total_clientes_unicos": len(set([d["cliente_id"] for d in deudores])),
            "total_adeudado": sum([d["saldo_pendiente"] for d in deudores]),
            "deudores": deudores,
            "resumen_por_origen": {
                "trabajos": total_trabajos,
                "manuales": total_deudas
            }
        }
        
    except Exception as e:
        print(f"Error en get_deudas_pendientes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CREAR DEUDA MANUAL (asigna sede activa)
# ============================================
@router.post("/deudas/manual/")
async def crear_deuda_manual_endpoint(
    request: Request,
    deuda_data: dict,
    db: Session = Depends(get_db),
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
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id, Cliente.activo == True).first()
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
        db.commit()
        db.refresh(nueva_deuda)
        
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
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PAGAR DEUDA MANUAL (solo deudas de la sede)
# ============================================
@router.put("/deudas/manual/{deuda_id}/pagar/")
async def pagar_deuda_manual(
    request: Request,
    deuda_id: int,
    pago_data: dict,
    db: Session = Depends(get_db),
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
        deuda = db.query(DeudaManual).filter(
            DeudaManual.id == deuda_id,
            DeudaManual.sede_id == sid
        ).first()
        if not deuda:
            raise HTTPException(status_code=404, detail="Deuda no encontrada")
        
        if deuda.estado == 'pagado':
            raise HTTPException(status_code=400, detail="Deuda ya pagada")
        
        if monto_pago > deuda.saldo_pendiente:
            raise HTTPException(status_code=400, detail="Monto excede el saldo pendiente")
        
        deuda.monto_pagado += monto_pago
        deuda.saldo_pendiente -= monto_pago
        
        if deuda.saldo_pendiente <= 0:
            deuda.estado = 'pagado'
        elif deuda.monto_pagado > 0:
            deuda.estado = 'parcial'
        
        deuda.fecha_actualizacion = datetime.utcnow()
        
        db.commit()
        db.refresh(deuda)
        
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
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))