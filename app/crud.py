# app/crud.py
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app import models
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import bcrypt


# === HASHING CON BCRYPT PURO ===
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hash_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)


# === USUARIOS ===
async def crear_usuario(db: AsyncSession, nombre: str, username: str, email: str, password: str, rol: str):
    """Crear un nuevo usuario"""
    hashed = get_password_hash(password)
    db_usuario = models.Usuario(
        nombre=nombre,
        username=username,
        email=email,
        hashed_password=hashed,
        rol=rol,
        activo=True,
        fecha_creacion=datetime.utcnow()
    )
    db.add(db_usuario)
    await db.commit()
    await db.refresh(db_usuario)
    return db_usuario

async def obtener_usuario_por_username(db: AsyncSession, username: str):
    """Obtener usuario por username"""
    result = await db.execute(
        select(models.Usuario).where(models.Usuario.username == username)
    )
    return result.scalar_one_or_none()

async def obtener_usuario_por_id(db: AsyncSession, usuario_id: int):
    """Obtener usuario por ID"""
    result = await db.execute(
        select(models.Usuario).where(models.Usuario.id == usuario_id)
    )
    return result.scalar_one_or_none()

async def obtener_usuarios(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtener lista de usuarios"""
    result = await db.execute(
        select(models.Usuario).offset(skip).limit(limit)
    )
    return result.scalars().all()


# === ROL ===
async def crear_rol(db: AsyncSession, nombre: str):
    """Crear un nuevo rol"""
    db_rol = models.Rol(nombre=nombre.lower().strip())
    db.add(db_rol)
    await db.commit()
    await db.refresh(db_rol)
    return db_rol

async def obtener_roles(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtener lista de roles"""
    result = await db.execute(
        select(models.Rol).offset(skip).limit(limit)
    )
    return result.scalars().all()


# === EMPLEADO ===
async def crear_empleado(db: AsyncSession, nombre_completo: str, tipo_contrato: str, 
                         salario_fijo: float = 0.0, rol_id: int = None, activo: bool = True):
    """Crear un nuevo empleado"""
    db_empleado = models.Empleado(
        nombre_completo=nombre_completo,
        tipo_contrato=tipo_contrato,
        salario_fijo=salario_fijo,
        rol_id=rol_id,
        activo=activo
    )
    db.add(db_empleado)
    await db.commit()
    await db.refresh(db_empleado)
    return db_empleado

async def obtener_empleados(db: AsyncSession, activo: Optional[bool] = True, skip: int = 0, limit: int = 100):
    """Obtener lista de empleados"""
    query = select(models.Empleado)
    if activo is not None:
        query = query.where(models.Empleado.activo == activo)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def obtener_empleado_por_id(db: AsyncSession, empleado_id: int):
    """Obtener empleado por ID"""
    result = await db.execute(
        select(models.Empleado).where(models.Empleado.id == empleado_id)
    )
    return result.scalar_one_or_none()


# === CLIENTE ===
async def crear_cliente(db: AsyncSession, tipo_cliente: str, nombre_razon_social: str,
                        telefono: str = None, email: str = None, direccion: str = None,
                        notas: str = None, activo: bool = True, **kwargs):
    """Crear un nuevo cliente"""
    db_cliente = models.Cliente(
        tipo_cliente=tipo_cliente,
        nombre_razon_social=nombre_razon_social,
        telefono=telefono,
        email=email,
        direccion=direccion,
        notas=notas,
        activo=activo,
        **kwargs
    )
    db.add(db_cliente)
    await db.commit()
    await db.refresh(db_cliente)
    return db_cliente

async def obtener_clientes(db: AsyncSession, skip: int = 0, limit: int = 100, activo: Optional[bool] = True):
    """Obtener lista de clientes"""
    query = select(models.Cliente)
    if activo is not None:
        query = query.where(models.Cliente.activo == activo)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def obtener_cliente_por_id(db: AsyncSession, cliente_id: int):
    """Obtener cliente por ID"""
    result = await db.execute(
        select(models.Cliente).where(models.Cliente.id == cliente_id)
    )
    return result.scalar_one_or_none()


# === TRABAJO ===
async def crear_trabajo(db: AsyncSession, cliente_id: int, nombre_trabajo: str,
                        monto_total: float, fecha_inicio: date, estado: str,
                        tipo_trabajo: str = "rotulado_instalacion", descripcion: str = None,
                        prioridad: str = "media", metros_cuadrados: float = None,
                        unidades: int = None, tasa_cambio: float = None,
                        presupuesto_id: int = None, creado_por: int = None):
    """Crear un nuevo trabajo"""
    db_trabajo = models.Trabajo(
        cliente_id=cliente_id,
        nombre_trabajo=nombre_trabajo,
        monto_total=monto_total,
        fecha_inicio=fecha_inicio,
        estado=estado,
        tipo_trabajo=tipo_trabajo,
        descripcion=descripcion,
        prioridad=prioridad,
        metros_cuadrados=metros_cuadrados,
        unidades=unidades,
        tasa_cambio=tasa_cambio,
        presupuesto_id=presupuesto_id,
        creado_por=creado_por,
        fecha_creacion=datetime.utcnow()
    )
    db.add(db_trabajo)
    await db.commit()
    await db.refresh(db_trabajo)
    return db_trabajo

async def obtener_trabajos(db: AsyncSession, skip: int = 0, limit: int = 100, estado: str = None):
    """Obtener lista de trabajos"""
    query = select(models.Trabajo)
    if estado:
        query = query.where(models.Trabajo.estado == estado)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def obtener_trabajo_por_id(db: AsyncSession, trabajo_id: int):
    """Obtener trabajo por ID"""
    result = await db.execute(
        select(models.Trabajo).where(models.Trabajo.id == trabajo_id)
    )
    return result.scalar_one_or_none()


# === ASIGNACIÓN ===
async def crear_asignacion(db: AsyncSession, trabajo_id: int, empleado_id: int, rol_id: int,
                           tipo_comision: str = "porcentaje", valor_unitario: float = None,
                           valor_comision: float = 0.0):
    """Crear una nueva asignación"""
    db_asignacion = models.Asignacion(
        trabajo_id=trabajo_id,
        empleado_id=empleado_id,
        rol_id=rol_id,
        tipo_comision=tipo_comision,
        valor_unitario=valor_unitario,
        valor_comision=valor_comision
    )
    db.add(db_asignacion)
    await db.commit()
    await db.refresh(db_asignacion)
    return db_asignacion

async def obtener_asignaciones_por_trabajo(db: AsyncSession, trabajo_id: int):
    """Obtener asignaciones de un trabajo"""
    result = await db.execute(
        select(models.Asignacion).where(models.Asignacion.trabajo_id == trabajo_id)
    )
    return result.scalars().all()


# === GASTOS DIARIOS ===
async def crear_gasto(db: AsyncSession, fecha: date, monto: float, descripcion: str,
                      categoria_id: int = None, subcategoria_id: int = None,
                      empleado_id: int = None, trabajo_id: int = None):
    """Crear un nuevo gasto diario"""
    db_gasto = models.GastoDiario(
        fecha=fecha,
        monto=monto,
        descripcion=descripcion,
        categoria_id=categoria_id,
        subcategoria_id=subcategoria_id,
        empleado_id=empleado_id,
        trabajo_id=trabajo_id
    )
    db.add(db_gasto)
    await db.commit()
    await db.refresh(db_gasto)
    return db_gasto

async def obtener_gastos_por_fecha(db: AsyncSession, fecha_inicio: date, fecha_fin: date):
    """Obtener gastos en un rango de fechas"""
    query = select(models.GastoDiario).where(
        models.GastoDiario.fecha.between(fecha_inicio, fecha_fin)
    )
    result = await db.execute(query)
    return result.scalars().all()


# === PRÉSTAMOS ===
async def crear_prestamo(db: AsyncSession, empleado_id: int, monto: float,
                         fecha: date, descripcion: str = None, pagado: bool = False):
    """Crear un nuevo préstamo"""
    db_prestamo = models.Prestamo(
        empleado_id=empleado_id,
        monto=monto,
        fecha=fecha,
        descripcion=descripcion,
        pagado=pagado
    )
    db.add(db_prestamo)
    await db.commit()
    await db.refresh(db_prestamo)
    return db_prestamo

async def obtener_prestamos_por_fecha(db: AsyncSession, fecha_inicio: date, fecha_fin: date):
    """Obtener préstamos en un rango de fechas"""
    result = await db.execute(
        select(models.Prestamo).where(
            models.Prestamo.fecha.between(fecha_inicio, fecha_fin)
        )
    )
    return result.scalars().all()


# === DEUDAS MANUALES (NUEVO) ===
async def crear_deuda_manual(db: AsyncSession, cliente_id: int, nombre_trabajo: str,
                            monto_deuda: float, observaciones: str = None,
                            creado_por: int = None):
    """Crear una nueva deuda manual"""
    db_deuda = models.DeudaManual(
        cliente_id=cliente_id,
        nombre_trabajo=nombre_trabajo,
        monto_deuda=monto_deuda,
        saldo_pendiente=monto_deuda,
        monto_pagado=0.0,
        estado="pendiente",
        observaciones=observaciones,
        creado_por=creado_por,
        fecha_registro=datetime.utcnow()
    )
    db.add(db_deuda)
    await db.commit()
    await db.refresh(db_deuda)
    return db_deuda

async def obtener_deudas_manuales(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Obtener lista de deudas manuales"""
    result = await db.execute(
        select(models.DeudaManual).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def obtener_deuda_manual_por_id(db: AsyncSession, deuda_id: int):
    """Obtener deuda manual por ID"""
    result = await db.execute(
        select(models.DeudaManual).where(models.DeudaManual.id == deuda_id)
    )
    return result.scalar_one_or_none()

async def registrar_pago_deuda_manual(db: AsyncSession, deuda_id: int, monto_pago: float):
    """Registrar un pago en una deuda manual"""
    deuda = await obtener_deuda_manual_por_id(db, deuda_id)
    if not deuda:
        return None
    
    if deuda.estado == 'pagado':
        raise ValueError("Esta deuda ya está completamente pagada")
    
    if monto_pago > deuda.saldo_pendiente:
        raise ValueError(f"El monto del pago excede el saldo pendiente")
    
    deuda.monto_pagado += monto_pago
    deuda.saldo_pendiente -= monto_pago
    
    if deuda.saldo_pendiente <= 0:
        deuda.estado = 'pagado'
    elif deuda.monto_pagado > 0:
        deuda.estado = 'parcial'
    
    deuda.fecha_actualizacion = datetime.utcnow()
    
    await db.commit()
    await db.refresh(deuda)
    return deuda


# === FUNCIONES DE CÁLCULO ===
async def calcular_comisiones_trabajo(db: AsyncSession, trabajo_id: int):
    """Calcular comisiones de un trabajo"""
    asignaciones = await obtener_asignaciones_por_trabajo(db, trabajo_id)
    trabajo = await obtener_trabajo_por_id(db, trabajo_id)
    
    if not trabajo:
        return []
    
    comisiones = []
    for asignacion in asignaciones:
        empleado = await obtener_empleado_por_id(db, asignacion.empleado_id)
        if not empleado:
            continue
            
        if asignacion.tipo_comision == "porcentaje":
            comision = float(trabajo.monto_total) * (float(asignacion.valor_comision) / 100)
        else:
            comision = float(asignacion.valor_comision)
        
        comisiones.append({
            "empleado_id": empleado.id,
            "nombre": empleado.nombre_completo,
            "comision": comision
        })
    
    return comisiones


# === REPORTE SEMANAL ===
async def generar_reporte_semanal(db: AsyncSession, inicio_semana: datetime, fin_semana: datetime):
    """
    Genera un reporte semanal de lunes 00:00 a sábado 19:00.
    """
    # 1. Obtener trabajos finalizados en el periodo
    query_trabajos = select(models.Trabajo).where(
        models.Trabajo.estado == "finalizado",
        models.Trabajo.fecha_inicio >= inicio_semana.date(),
        models.Trabajo.fecha_inicio <= fin_semana.date()
    )
    trabajos = (await db.execute(query_trabajos)).scalars().all()

    # 2. Calcular comisiones por empleado
    comisiones_por_empleado = {}
    total_comisiones = 0.0

    for trabajo in trabajos:
        comisiones = await calcular_comisiones_trabajo(db, trabajo.id)
        for c in comisiones:
            emp_id = c["empleado_id"]
            if emp_id not in comisiones_por_empleado:
                comisiones_por_empleado[emp_id] = {
                    "nombre": c["nombre"],
                    "total": 0,
                    "detalles": []
                }
            comisiones_por_empleado[emp_id]["total"] += c["comision"]
            comisiones_por_empleado[emp_id]["detalles"].append({
                "trabajo_id": trabajo.id,
                "trabajo_nombre": trabajo.nombre_trabajo,
                "comision": c["comision"]
            })
            total_comisiones += c["comision"]

    # 3. Obtener gastos
    gastos = await db.execute(
        select(models.GastoDiario).where(
            models.GastoDiario.fecha >= inicio_semana.date(),
            models.GastoDiario.fecha <= fin_semana.date()
        )
    )
    gastos = gastos.scalars().all()
    total_gastos = sum(float(g.monto) for g in gastos)

    # 4. Obtener préstamos
    prestamos = await db.execute(
        select(models.Prestamo).where(
            models.Prestamo.fecha >= inicio_semana.date(),
            models.Prestamo.fecha <= fin_semana.date()
        )
    )
    prestamos = prestamos.scalars().all()
    
    deducciones_por_empleado = {}
    for p in prestamos:
        emp_id = p.empleado_id
        empleado = await obtener_empleado_por_id(db, emp_id)
        if emp_id not in deducciones_por_empleado:
            deducciones_por_empleado[emp_id] = {
                "nombre": empleado.nombre_completo if empleado else "Desconocido",
                "total": 0,
                "detalles": []
            }
        deducciones_por_empleado[emp_id]["total"] += float(p.monto)
        deducciones_por_empleado[emp_id]["detalles"].append({
            "fecha": p.fecha.isoformat(),
            "monto": float(p.monto),
            "descripcion": p.descripcion
        })

    # 5. Ajustar comisiones netas
    for emp_id, info in comisiones_por_empleado.items():
        deduccion = deducciones_por_empleado.get(emp_id, {}).get("total", 0)
        info["comision_neta"] = round(info["total"] - deduccion, 2)
        info["deduccion"] = round(deduccion, 2)

    # 6. Preparar datos del reporte
    reporte_data = {
        "periodo": {
            "inicio": inicio_semana.isoformat(),
            "fin": fin_semana.isoformat()
        },
        "total_comisiones": round(total_comisiones, 2),
        "total_gastos": round(total_gastos, 2),
        "trabajos_finalizados": len(trabajos),
        "comisiones_por_empleado": {
            str(emp_id): {
                "nombre": info["nombre"],
                "total": round(info["total"], 2),
                "comision_neta": info["comision_neta"],
                "deduccion": info["deduccion"],
                "detalles": info["detalles"]
            }
            for emp_id, info in comisiones_por_empleado.items()
        },
        "deducciones_por_empleado": deducciones_por_empleado,
        "gastos": [
            {
                "fecha": g.fecha.isoformat(),
                "monto": float(g.monto),
                "descripcion": g.descripcion,
                "categoria": g.categoria_id
            }
            for g in gastos
        ]
    }

    # 7. Guardar en BD
    db_reporte = models.ReporteSemanal(
        semana_inicio=inicio_semana.date(),
        semana_fin=fin_semana.date(),
        datos=reporte_data
    )
    db.add(db_reporte)
    await db.commit()
    await db.refresh(db_reporte)
    return reporte_data


async def generar_reporte_diario(db: AsyncSession, fecha: date):
    """Generar reporte diario"""
    # 1. Trabajos finalizados HOY
    query_trabajos = select(models.Trabajo).where(
        models.Trabajo.estado == "finalizado",
        models.Trabajo.fecha_inicio == fecha
    )
    result = await db.execute(query_trabajos)
    trabajos = result.scalars().all()
    
    ingresos = 0.0
    comisiones_detalle = []
    for t in trabajos:
        comisiones = await calcular_comisiones_trabajo(db, t.id)
        for c in comisiones:
            ingresos += c["comision"]
            comisiones_detalle.append(c)

    # 2. Gastos
    result_gastos = await db.execute(
        select(models.GastoDiario).where(models.GastoDiario.fecha == fecha)
    )
    gastos = result_gastos.scalars().all()
    total_gastos = sum(float(g.monto) for g in gastos)

    # 3. Préstamos
    result_prestamos = await db.execute(
        select(models.Prestamo).where(models.Prestamo.fecha == fecha)
    )
    prestamos = result_prestamos.scalars().all()
    total_prestamos = sum(float(p.monto) for p in prestamos)

    egresos = total_gastos + total_prestamos
    saldo = ingresos - egresos

    return {
        "fecha": fecha.isoformat(),
        "ingresos": round(ingresos, 2),
        "egresos": round(egresos, 2),
        "saldo": round(saldo, 2),
        "detalle": {
            "comisiones": comisiones_detalle,
            "gastos": [
                {"descripcion": g.descripcion or "Sin descripción", "monto": float(g.monto)}
                for g in gastos
            ],
            "prestamos": [
                {"empleado": p.empleado.nombre_completo, "monto": float(p.monto), "motivo": p.descripcion or "-"}
                for p in prestamos
            ]
        }
    }


async def obtener_clientes(db: AsyncSession, skip: int = 0, limit: int = 100, activo: Optional[bool] = True):
    """Obtener lista de clientes"""
    query = select(models.Cliente)
    if activo is not None:
        query = query.where(models.Cliente.activo == activo)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()