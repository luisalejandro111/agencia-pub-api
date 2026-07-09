# app/api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, database
from datetime import date
from typing import List

router = APIRouter()


# === ROL ===
@router.post("/roles/", response_model=schemas.RolResponse)
async def crear_rol(
    rol: schemas.RolCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Crear un nuevo rol"""
    try:
        return await crud.crear_rol(db, rol.nombre)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear rol: {str(e)}"
        )


@router.get("/roles/", response_model=List[schemas.RolResponse])
async def leer_roles(
    db: AsyncSession = Depends(database.get_db)
):
    """Obtener todos los roles"""
    return await crud.obtener_roles(db)


# === EMPLEADO ===
@router.post("/empleados/", response_model=schemas.EmpleadoResponse)
async def crear_empleado(
    empleado: schemas.EmpleadoCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Crear un nuevo empleado"""
    try:
        return await crud.crear_empleado(
            db=db,
            nombre_completo=empleado.nombre_completo,
            tipo_contrato=empleado.tipo_contrato,
            salario_fijo=empleado.salario_fijo or 0.0,
            rol_id=empleado.rol_id,
            activo=empleado.activo if hasattr(empleado, 'activo') else True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear empleado: {str(e)}"
        )


@router.get("/empleados/", response_model=List[schemas.EmpleadoResponse])
async def leer_empleados(
    activo: bool = True,
    db: AsyncSession = Depends(database.get_db)
):
    """Obtener lista de empleados"""
    return await crud.obtener_empleados(db, activo=activo)


# === TRABAJO ===
@router.post("/trabajos/", response_model=schemas.TrabajoResponse)
async def crear_trabajo(
    trabajo: schemas.TrabajoCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Crear un nuevo trabajo"""
    try:
        return await crud.crear_trabajo(db, **trabajo.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear trabajo: {str(e)}"
        )


@router.get("/trabajos/", response_model=List[schemas.TrabajoResponse])
async def leer_trabajos(
    db: AsyncSession = Depends(database.get_db)
):
    """Obtener lista de trabajos"""
    return await crud.obtener_trabajos(db)


@router.post("/trabajos/{trabajo_id}/asignaciones/", response_model=dict)
async def agregar_asignacion(
    trabajo_id: int,
    asignacion: schemas.AsignacionCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Agregar una asignación a un trabajo"""
    try:
        await crud.crear_asignacion(
            db=db,
            trabajo_id=trabajo_id,
            empleado_id=asignacion.empleado_id,
            rol_id=asignacion.rol_id,
            tipo_comision=asignacion.tipo_comision if hasattr(asignacion, 'tipo_comision') else "porcentaje",
            valor_unitario=asignacion.valor_unitario if hasattr(asignacion, 'valor_unitario') else None,
            valor_comision=asignacion.valor_comision if hasattr(asignacion, 'valor_comision') else 0.0
        )
        return {"mensaje": "Asignación agregada exitosamente", "trabajo_id": trabajo_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al agregar asignación: {str(e)}"
        )


# === CALCULAR COMISIONES ===
@router.get("/trabajos/{trabajo_id}/comisiones/", response_model=List[dict])
async def ver_comisiones_trabajo(
    trabajo_id: int,
    db: AsyncSession = Depends(database.get_db)
):
    """Calcular comisiones de un trabajo"""
    comisiones = await crud.calcular_comisiones_trabajo(db, trabajo_id)
    if not comisiones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trabajo no finalizado o sin asignaciones"
        )
    return comisiones


# === TRABAJO COMPLETO ===
@router.post("/trabajos/completo/", response_model=schemas.TrabajoResponse)
async def crear_trabajo_completo(
    trabajo_completo: dict,  # Cambiar por un esquema específico si lo tienes
    db: AsyncSession = Depends(database.get_db)
):
    """Crear un trabajo completo con todos sus datos"""
    try:
        # Aquí deberías tener un esquema TrabajoCompletoCreate
        # Por ahora asumimos que viene un dict con todos los datos
        return await crud.crear_trabajo(db, **trabajo_completo)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear trabajo completo: {str(e)}"
        )


# === GASTOS DIARIOS ===
@router.post("/gastos/", response_model=schemas.GastoDiarioResponse)
async def crear_gasto(
    gasto: schemas.GastoDiarioCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Crear un nuevo gasto diario"""
    try:
        return await crud.crear_gasto(
            db=db,
            fecha=gasto.fecha,
            monto=gasto.monto,
            descripcion=gasto.descripcion,
            categoria_id=gasto.categoria_id if hasattr(gasto, 'categoria_id') else None,
            subcategoria_id=gasto.subcategoria_id if hasattr(gasto, 'subcategoria_id') else None,
            empleado_id=gasto.empleado_id if hasattr(gasto, 'empleado_id') else None,
            trabajo_id=gasto.trabajo_id if hasattr(gasto, 'trabajo_id') else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear gasto: {str(e)}"
        )


# === USUARIOS ===
@router.post("/usuarios/", response_model=schemas.UsuarioResponse)
async def crear_usuario(
    usuario: schemas.UsuarioCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Crear un nuevo usuario"""
    try:
        return await crud.crear_usuario(
            db=db,
            nombre=usuario.nombre,
            username=usuario.username,
            email=usuario.email,
            password=usuario.password,
            rol=usuario.rol
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear usuario: {str(e)}"
        )


# === DEUDAS MANUALES (NUEVO) ===
@router.post("/deudas/manual/", response_model=schemas.DeudaManualResponse)
async def crear_deuda_manual(
    deuda: schemas.DeudaManualCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Crear una nueva deuda manual"""
    try:
        return await crud.crear_deuda_manual(
            db=db,
            cliente_id=deuda.cliente_id,
            nombre_trabajo=deuda.nombre_trabajo,
            monto_deuda=deuda.monto_deuda,
            observaciones=deuda.observaciones if hasattr(deuda, 'observaciones') else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear deuda manual: {str(e)}"
        )


@router.get("/deudas/manual/", response_model=List[schemas.DeudaManualResponse])
async def leer_deudas_manuales(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db)
):
    """Obtener lista de deudas manuales"""
    return await crud.obtener_deudas_manuales(db, skip=skip, limit=limit)


@router.post("/deudas/manual/{deuda_id}/pagar/", response_model=schemas.DeudaManualResponse)
async def registrar_pago_deuda_manual(
    deuda_id: int,
    pago: schemas.DeudaManualUpdate,
    db: AsyncSession = Depends(database.get_db)
):
    """Registrar un pago en una deuda manual"""
    try:
        return await crud.registrar_pago_deuda_manual(
            db=db,
            deuda_id=deuda_id,
            monto_pago=pago.monto_pago
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar pago: {str(e)}"
        )


# === REPORTES ===
@router.get("/reportes/semanal/")
async def generar_reporte_semanal(
    inicio: str,
    fin: str,
    db: AsyncSession = Depends(database.get_db)
):
    """Generar reporte semanal"""
    try:
        from datetime import datetime
        inicio_date = datetime.fromisoformat(inicio)
        fin_date = datetime.fromisoformat(fin)
        return await crud.generar_reporte_semanal(db, inicio_date, fin_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al generar reporte: {str(e)}"
        )


@router.get("/reportes/diario/")
async def generar_reporte_diario(
    fecha: str,
    db: AsyncSession = Depends(database.get_db)
):
    """Generar reporte diario"""
    try:
        from datetime import date as date_type
        fecha_date = date_type.fromisoformat(fecha)
        return await crud.generar_reporte_diario(db, fecha_date)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al generar reporte: {str(e)}"
        )



# === CLIENTES ===
@router.get("/clientes/activos", response_model=List[schemas.ClienteResponse])
async def obtener_clientes_activos(
    db: AsyncSession = Depends(database.get_db)
):
    """Obtener todos los clientes activos"""
    return await crud.obtener_clientes(db, activo=True)