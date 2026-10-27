# app/models.py
from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, Date, DateTime, ForeignKey, Float, CheckConstraint, Text, func, Numeric, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, JSON
from datetime import datetime, date, time
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from app.database import Base


# ============================================
# 🏢 MÓDULO: SEDES (SUCURSALES) - NUEVO
# ============================================

class Sede(Base):
    __tablename__ = "sedes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(200), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    encargado = Column(String(100), nullable=True)
    activa = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    usuarios = relationship("Usuario", back_populates="sede")
    clientes = relationship("Cliente", back_populates="sede")
    empleados = relationship("Empleado", back_populates="sede")
    trabajos = relationship("Trabajo", back_populates="sede")
    presupuestos = relationship("Presupuesto", back_populates="sede")
    stocks = relationship("StockSede", back_populates="sede")
    entradas = relationship("EntradaInventario", back_populates="sede")
    salidas = relationship("SalidaMaterial", back_populates="sede")
    movimientos = relationship("MovimientoInventario", back_populates="sede")
    gastos = relationship("GastoDiario", back_populates="sede")
    ingresos = relationship("IngresoDiario", back_populates="sede")
    cierres_caja = relationship("CierreCaja", back_populates="sede")
    activos = relationship("ActivoFijo", back_populates="sede")
    asistencias = relationship("Asistencia", back_populates="sede")
    deudas = relationship("DeudaManual", back_populates="sede")
    pagos_trabajo = relationship("PagoTrabajo", back_populates="sede")
    servicios_externos = relationship("ServicioExterno", back_populates="sede")
    prestamos = relationship("Prestamo", back_populates="sede")
    material_usado = relationship("MaterialUsado", back_populates="sede")
    deducciones = relationship("DeduccionEmpleado", back_populates="sede")
    pagos_semanales = relationship("PagoSemanal", back_populates="sede")
    compras_empleado = relationship("CompraEmpleado", back_populates="sede")
    reportes_semanales = relationship("ReporteSemanal", back_populates="sede")
    movimientos_activo = relationship("MovimientoActivoFijo", back_populates="sede")

    # Transferencias
    transferencias_origen = relationship(
        "TransferenciaInventario",
        foreign_keys="TransferenciaInventario.origen_sede_id",
        back_populates="sede_origen"
    )
    transferencias_destino = relationship(
        "TransferenciaInventario",
        foreign_keys="TransferenciaInventario.destino_sede_id",
        back_populates="sede_destino"
    )


    categorias_inventario = relationship("CategoriaInventario", back_populates="sede")


class StockSede(Base):
    """Stock de cada material en cada sede"""
    __tablename__ = "stock_sede"

    id = Column(Integer, primary_key=True, index=True)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=False)
    stock_actual = Column(Float, default=0.0, nullable=False)
    stock_minimo = Column(Float, default=0.0, nullable=False)
    tallas = Column(JSON, nullable=True)
    ubicacion = Column(String(100), nullable=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sede = relationship("Sede", back_populates="stocks")
    material = relationship("MaterialInventario", back_populates="stocks_sede")

    __table_args__ = (
        UniqueConstraint('sede_id', 'material_id', name='uq_sede_material'),
    )


class TransferenciaInventario(Base):
    """Movimiento de materiales entre sedes"""
    __tablename__ = "transferencias_inventario"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), unique=True, nullable=False)

    origen_sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    destino_sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=False)

    cantidad = Column(Float, nullable=False)
    tallas_detalle = Column(JSON, nullable=True)

    estado = Column(String(20), default="pendiente", nullable=False)
    motivo = Column(String(200), nullable=True)

    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    recibido_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_envio = Column(DateTime, nullable=True)
    fecha_recepcion = Column(DateTime, nullable=True)

    sede_origen = relationship("Sede", foreign_keys=[origen_sede_id], back_populates="transferencias_origen")
    sede_destino = relationship("Sede", foreign_keys=[destino_sede_id], back_populates="transferencias_destino")
    material = relationship("MaterialInventario", back_populates="transferencias")
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id], back_populates="transferencias_creadas")
    recibido_por = relationship("Usuario", foreign_keys=[recibido_por_id], back_populates="transferencias_recibidas")


# ============================================
# 👤 USUARIOS Y EMPLEADOS
# ============================================

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    rol = Column(String(20), nullable=False)  # "superadmin", "administrador", "operativo", "contable"
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # 🔥 SEDE + SUPERADMIN
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)
    es_superadmin = Column(Boolean, default=False)

    empleado_id = Column(Integer, ForeignKey("empleado.id", ondelete="SET NULL"), nullable=True)

    # Relaciones
    empleado = relationship("Empleado", back_populates="usuario")
    sede = relationship("Sede", back_populates="usuarios")

    # Transferencias
    transferencias_creadas = relationship(
        "TransferenciaInventario",
        foreign_keys="TransferenciaInventario.creado_por_id",
        back_populates="creado_por"
    )
    transferencias_recibidas = relationship(
        "TransferenciaInventario",
        foreign_keys="TransferenciaInventario.recibido_por_id",
        back_populates="recibido_por"
    )


class Rol(Base):
    """🌐 GLOBAL - Sin sede_id"""
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    asignaciones = relationship("Asignacion", back_populates="rol")


class Empleado(Base):
    __tablename__ = "empleado"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(100), nullable=False)
    tipo_contrato = Column(String(20), nullable=False)
    sueldo_fijo = Column("salario_fijo", DECIMAL(10, 2), default=0.0, nullable=True)
    activo = Column(Boolean, default=True)
    rol_id = Column(Integer, ForeignKey("rol.id", ondelete="SET NULL"))

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    hora_entrada_default = Column(Time, default=time(9, 0))
    hora_salida_default = Column(Time, default=time(18, 0))
    bono_puntualidad_acumulado = Column(DECIMAL(10, 2), default=0.0)
    tiene_acceso_qr = Column(Boolean, default=True)

    # Relaciones
    rol = relationship("Rol")
    asignaciones = relationship("Asignacion", back_populates="empleado")
    cliente = relationship("Cliente", back_populates="empleado", uselist=False)
    compras = relationship("CompraEmpleado", back_populates="empleado")
    asistencias = relationship("Asistencia", back_populates="empleado")
    usuario = relationship("Usuario", back_populates="empleado", uselist=False)
    sede = relationship("Sede", back_populates="empleados")


# ============================================
# 👥 CLIENTES
# ============================================

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    tipo_cliente = Column(String(20), nullable=False)

    nombre_razon_social = Column(String(150), nullable=False)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    notas = Column(Text)
    activo = Column(Boolean, default=True)

    cedula = Column(String(20))
    primer_nombre = Column(String(50))
    segundo_nombre = Column(String(50))
    primer_apellido = Column(String(50))
    segundo_apellido = Column(String(50))

    rif = Column(String(20))
    representante_legal = Column(String(100))
    telefono_empresa = Column(String(20))
    sitio_web = Column(String(100))

    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=True)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    empleado = relationship("Empleado", foreign_keys=[empleado_id])
    trabajos = relationship("Trabajo", back_populates="cliente")
    sede = relationship("Sede", back_populates="clientes")


# ============================================
# 💼 TRABAJOS Y PRESUPUESTOS
# ============================================

class TipoTrabajo(Base):
    """🌐 GLOBAL - Sin sede_id"""
    __tablename__ = "tipos_trabajo"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255))
    activo = Column(Boolean, default=True)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    numero_presupuesto = Column(String(50), unique=True, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    nombre_trabajo = Column(String(200), nullable=False)
    tipo_trabajo_id = Column(Integer, ForeignKey("tipos_trabajo.id"))
    estado = Column(String(20), default="borrador")
    observaciones = Column(Text)
    validez_dias = Column(Integer, default=15)
    total_base = Column(DECIMAL(12, 2), nullable=False, default=0.0)
    total_cliente = Column(DECIMAL(12, 2), nullable=False, default=0.0)
    tasa_aplicada = Column(DECIMAL(10, 2))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_envio = Column(DateTime)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))

    cliente = relationship("Cliente")
    tipo_trabajo = relationship("TipoTrabajo")
    items_cliente = relationship("ItemPresupuestoCliente", cascade="all, delete-orphan")
    items_internos = relationship("ItemPresupuestoInterno", cascade="all, delete-orphan")
    trabajos = relationship("Trabajo", back_populates="presupuesto")
    sede = relationship("Sede", back_populates="presupuestos")


class ItemPresupuestoCliente(Base):
    """🌐 Hereda sede del presupuesto - Sin sede_id"""
    __tablename__ = "items_presupuesto_cliente"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    concepto = Column(String(200), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    orden = Column(Integer, default=0)


class ItemPresupuestoInterno(Base):
    """🌐 Hereda sede del presupuesto - Sin sede_id"""
    __tablename__ = "items_presupuesto_interno"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    tipo_item = Column(String(30), nullable=False)
    descripcion = Column(String(200), nullable=False)
    costo = Column(DECIMAL(10, 2), nullable=False)
    orden = Column(Integer, default=0)


class ItemPresupuesto(Base):
    """🌐 Hereda sede del presupuesto - Sin sede_id"""
    __tablename__ = "items_presupuesto"

    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"))
    concepto = Column(String(200), nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    cantidad = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    unidad_medida = Column(String(20), nullable=False)


class Trabajo(Base):
    __tablename__ = "trabajo"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    nombre_trabajo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    prioridad = Column(String(20), default="media")
    estado = Column(String(50), nullable=False, default="pendiente")
    tipo_trabajo_id = Column(Integer, ForeignKey("tipos_trabajo.id"), nullable=True)
    estructura = Column(String(50), default="sin_estructura")

    metros_cuadrados = Column(DECIMAL(8, 2), default=0.0)
    unidades = Column(Integer, default=0)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_finalizacion = Column(DateTime, nullable=True)
    fecha_entrega = Column(DateTime, nullable=True)

    monto_total = Column(DECIMAL(12, 2), nullable=False, default=0.0)
    monto_total_usd = Column(DECIMAL(12, 2), default=0.0)
    monto_total_bs = Column(DECIMAL(12, 2), default=0.0)

    monto_pagado = Column(DECIMAL(12, 2), default=0.0)
    monto_pagado_usd = Column(DECIMAL(12, 2), default=0.0)
    monto_pagado_bs = Column(DECIMAL(15, 2), default=0.0)
    porcentaje_pagado = Column(DECIMAL(5, 2), default=0.0)

    tasa_cambio = Column(DECIMAL(10, 4), default=1.0)
    tasa_cambio_actual = Column(DECIMAL(10, 4), default=1.0)

    metodo_pago = Column(String(50), nullable=True)
    fecha_pago = Column(DateTime, nullable=True)

    total_presupuestado = Column(DECIMAL(12, 2), default=0.0)
    total_materiales_usd = Column(DECIMAL(12, 2), default=0.0)
    total_comisiones_usd = Column(DECIMAL(12, 2), default=0.0)
    servicios_externos_usd = Column(DECIMAL(12, 2), default=0.0)
    ganancia_neta_usd = Column(DECIMAL(12, 2), default=0.0)

    total_materiales_bs = Column(DECIMAL(12, 2), default=0.0)
    total_comisiones_bs = Column(DECIMAL(12, 2), default=0.0)
    servicios_externos_bs = Column(DECIMAL(12, 2), default=0.0)
    ganancia_neta_bs = Column(DECIMAL(12, 2), default=0.0)

    entregado = Column(Boolean, default=False)
    materiales_usados = Column(JSON, nullable=True)

    papel_sublimacion_nombre = Column(String(200), nullable=True)
    papel_sublimacion_cantidad = Column(String(50), nullable=True)

    # Relaciones
    archivos = relationship("ArchivoTrabajo", back_populates="trabajo", cascade="all, delete-orphan")
    servicios_externos = relationship("ServicioExterno", back_populates="trabajo", cascade="all, delete-orphan")
    asignaciones = relationship("Asignacion", back_populates="trabajo", cascade="all, delete-orphan")
    pagos = relationship("PagoTrabajo", back_populates="trabajo", cascade="all, delete-orphan")
    cliente = relationship("Cliente")
    presupuesto = relationship("Presupuesto")
    creador = relationship("Usuario", foreign_keys=[creado_por])
    tipo_trabajo = relationship("TipoTrabajo")
    sede = relationship("Sede", back_populates="trabajos")


class PagoTrabajo(Base):
    __tablename__ = "pagos_trabajo"

    id = Column(Integer, primary_key=True, index=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    metodo_pago = Column(String(50), nullable=False)
    monto_usd = Column(DECIMAL(12, 2), default=0.0)
    monto_bs = Column(DECIMAL(15, 2), default=0.0)
    tasa_cambio = Column(DECIMAL(10, 4), default=1.0)
    referencia = Column(String(255), nullable=True)
    fecha_pago = Column(DateTime, default=datetime.utcnow)

    trabajo = relationship("Trabajo", back_populates="pagos")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    sede = relationship("Sede", back_populates="pagos_trabajo")


class ServicioExterno(Base):
    __tablename__ = "servicios_externos"

    id = Column(Integer, primary_key=True, index=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    concepto = Column(String(200), nullable=False)
    proveedor = Column(String(200), nullable=True)
    costo = Column(DECIMAL(10, 2), nullable=False, default=0.0)
    fecha_creacion = Column(DateTime, default=datetime.now)

    trabajo = relationship("Trabajo", back_populates="servicios_externos")
    sede = relationship("Sede", back_populates="servicios_externos")


class ArchivoTrabajo(Base):
    """🌐 Hereda sede del trabajo - Sin sede_id"""
    __tablename__ = "archivo_trabajo"

    id = Column(Integer, primary_key=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    nombre_guardado = Column(String(255), nullable=False)
    ruta_completa = Column(String(500), nullable=False)
    tipo_mime = Column(String(100), nullable=False)
    tamano_bytes = Column(Integer, nullable=False)
    fecha_subida = Column(DateTime, default=datetime.utcnow)
    descripcion = Column(Text, nullable=True)

    trabajo = relationship("Trabajo", back_populates="archivos")


class Asignacion(Base):
    """🌐 Hereda sede del trabajo - Sin sede_id"""
    __tablename__ = "asignacion"

    id = Column(Integer, primary_key=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)
    rol_id = Column(Integer, ForeignKey("rol.id"), nullable=False)
    tipo_comision = Column(String(20), default="porcentaje")
    valor_unitario = Column(DECIMAL(10, 2))
    valor_comision = Column(DECIMAL(8, 2), nullable=False, default=0.0)

    trabajo = relationship("Trabajo", back_populates="asignaciones")
    empleado = relationship("Empleado", back_populates="asignaciones")
    rol = relationship("Rol", back_populates="asignaciones")


class TrabajoMaterialTextil(Base):
    """🌐 Hereda sede del trabajo - Sin sede_id"""
    __tablename__ = "trabajos_materiales_textiles"

    id = Column(Integer, primary_key=True, index=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    prenda = Column(String(200))
    talla = Column(String(50))
    cantidad = Column(Integer, default=1)
    m2_por_prenda = Column(Numeric(10, 4), default=0.0)
    tela_nombre = Column(String(200))
    tela_cantidad = Column(String(50))
    papel_nombre = Column(String(200))
    papel_cantidad = Column(String(50))
    tinta_nombre = Column(String(200))
    tinta_cantidad = Column(String(50))
    precio_unitario = Column(Numeric(10, 2), default=0.0)
    subtotal = Column(Numeric(10, 2), default=0.0)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    trabajo = relationship("Trabajo", foreign_keys=[trabajo_id])


# ============================================
# 📦 INVENTARIO
# ============================================

class CategoriaInventario(Base):
    __tablename__ = "categoria_inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(500))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # 🔥 NUEVO: Relación con sede para filtrado multi-sucursal
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)
    sede = relationship("Sede", back_populates="categorias_inventario")
    
    # Relación existente con materiales
    materiales = relationship("MaterialInventario", back_populates="categoria")


class Proveedor(Base):
    """🌐 GLOBAL - Sin sede_id (proveedores sirven a todas las sedes)"""
    __tablename__ = "proveedor"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    contacto = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(String(255))
    ruc = Column(String(20))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

    entradas = relationship("EntradaInventario", back_populates="proveedor")


class MaterialInventario(Base):
    """🌐 Catálogo global - El stock por sede vive en StockSede"""
    __tablename__ = "material_inventario"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categoria_inventario.id"), nullable=False)
    unidad_medida = Column(String(20), nullable=False)
    m2_por_unidad = Column(Float, default=1.0)

    # ⚠️ MANTENER por compatibilidad durante migración
    stock_actual = Column(Float, default=0.0, nullable=False)
    stock_minimo = Column(Float, default=0.0, nullable=False)

    precio_compra = Column(DECIMAL(10, 2), default=0.00)
    ubicacion = Column(String(100))
    observaciones = Column(Text)
    tallas = Column(JSON)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activo = Column(Boolean, default=True)
    precio_venta = Column(DECIMAL(10, 2), default=0.00)

    # Relaciones existentes
    categoria = relationship("CategoriaInventario", back_populates="materiales")
    movimientos = relationship("MovimientoInventario", back_populates="material")
    entradas = relationship("EntradaInventario", back_populates="material")
    salidas = relationship("SalidaMaterial", back_populates="material")
    usos = relationship("MaterialUsado", back_populates="material")

    # 🔥 NUEVO: Relaciones con sedes
    stocks_sede = relationship("StockSede", back_populates="material")
    transferencias = relationship("TransferenciaInventario", back_populates="material")


class InventarioMaterial(Base):
    """Legacy - mantener para compatibilidad"""
    __tablename__ = "inventario_material"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True)
    cantidad_disponible = Column(DECIMAL(10, 2), default=0.0)


class EntradaInventario(Base):
    __tablename__ = "entrada_inventario"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"))

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    cantidad = Column(Float, nullable=False)
    tallas_detalle = Column(JSON, nullable=True)
    precio_compra = Column(DECIMAL(10, 2), nullable=False)
    numero_factura = Column(String(50))
    fecha_entrada = Column(DateTime, default=datetime.utcnow)
    observaciones = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    material = relationship("MaterialInventario", back_populates="entradas")
    proveedor = relationship("Proveedor", back_populates="entradas")
    sede = relationship("Sede", back_populates="entradas")


class SalidaMaterial(Base):
    __tablename__ = "salida_material"

    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("material_inventario.id"))

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    cantidad = Column(DECIMAL(10, 2))
    tipo_salida = Column(String(50))
    motivo = Column(Text)
    referencia_id = Column(Integer)
    tipo_referencia = Column(String(50))
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_salida = Column(DateTime, default=datetime.utcnow)

    material = relationship("MaterialInventario", back_populates="salidas")
    sede = relationship("Sede", back_populates="salidas")


class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    tipo = Column(String(20), nullable=False)
    cantidad = Column(Float, nullable=False)
    motivo = Column(String(200), nullable=False)
    referencia = Column(String(100))
    fecha = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    observaciones = Column(Text)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"))

    material = relationship("MaterialInventario", back_populates="movimientos")
    trabajo = relationship("Trabajo")
    usuario = relationship("Usuario")
    sede = relationship("Sede", back_populates="movimientos")


class MaterialUsado(Base):
    __tablename__ = "material_usado"

    id = Column(Integer, primary_key=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=True)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    concepto = Column(String(200), nullable=True)
    cantidad_usada = Column(DECIMAL(10, 2), nullable=False)
    costo_unitario = Column(DECIMAL(12, 2), nullable=True)
    precio_unitario = Column(DECIMAL(10, 2), default=0.0)
    subtotal = Column(DECIMAL(10, 2), default=0.0)

    material = relationship("MaterialInventario", back_populates="usos")
    sede = relationship("Sede", back_populates="material_usado")


# ============================================
# 💰 FINANZAS: GASTOS, INGRESOS, CAJA
# ============================================

class CategoriaGasto(Base):
    """🌐 GLOBAL - Sin sede_id"""
    __tablename__ = "categoria_gasto"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(String(200))
    orden = Column(Integer, default=0)
    activa = Column(Boolean, default=True)


class SubcategoriaGasto(Base):
    """🌐 GLOBAL - Sin sede_id"""
    __tablename__ = "subcategoria_gasto"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categoria_gasto.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(200))
    orden = Column(Integer, default=0)
    activa = Column(Boolean, default=True)

    categoria = relationship("CategoriaGasto")


class GastoDiario(Base):
    __tablename__ = "gasto_diario"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    fecha = Column(Date, nullable=False, default=date.today())
    monto = Column(DECIMAL(10, 2), nullable=False)
    descripcion = Column(String(255))
    categoria_id = Column(Integer, ForeignKey("categoria_gasto.id"), default=4)
    subcategoria_id = Column(Integer, ForeignKey("subcategoria_gasto.id"), default=4)
    empleado_id = Column(Integer, ForeignKey("empleado.id"))
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"))

    categoria = relationship("CategoriaGasto", foreign_keys=[categoria_id])
    subcategoria = relationship("SubcategoriaGasto", foreign_keys=[subcategoria_id])
    sede = relationship("Sede", back_populates="gastos")


class IngresoDiario(Base):
    __tablename__ = 'ingreso_diario'

    id = Column(Integer, primary_key=True)
    cierre_caja_id = Column(Integer, ForeignKey('cierre_caja.id'), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    trabajo_id = Column(Integer, ForeignKey('trabajo.id'))
    presupuesto_id = Column(Integer, ForeignKey('presupuestos.id'))
    concepto = Column(String(200), nullable=False)
    monto_usd = Column(DECIMAL(10, 2), nullable=False)
    monto_bs = Column(DECIMAL(15, 2), nullable=False)
    metodo_pago = Column(String(50), nullable=False)
    referencia = Column(String(100))
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    observaciones = Column(Text)
    activo = Column(Boolean, default=True)

    cierre_caja = relationship("CierreCaja")
    cliente = relationship("Cliente")
    trabajo = relationship("Trabajo")
    presupuesto = relationship("Presupuesto")
    sede = relationship("Sede", back_populates="ingresos")


class CierreCaja(Base):
    __tablename__ = "cierre_caja"

    id = Column(Integer, primary_key=True)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    fecha = Column(Date, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    caja_inicial_usd = Column(Numeric(10, 2), default=0.0)
    caja_inicial_bs = Column(Numeric(10, 2), default=0.0)
    caja_final_real_usd = Column(Numeric(10, 2), default=0.0)
    caja_final_real_bs = Column(Numeric(10, 2), default=0.0)
    total_egresos_usd = Column(Numeric(10, 2), default=0.0)
    total_egresos_bs = Column(Numeric(10, 2), default=0.0)
    diferencia_usd = Column(Numeric(10, 2), default=0.0)
    diferencia_bs = Column(Numeric(10, 2), default=0.0)
    total_ingresos_usd = Column(Numeric(10, 2), default=0.0)
    total_ingresos_bs = Column(Numeric(10, 2), default=0.0)
    tasa_cambio = Column(Numeric(10, 4), nullable=False)
    fecha_cierre = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    pagos_usd_directos = Column(Float, default=0)
    pagos_bs_convertidos_usd = Column(Float, default=0)
    pagos_bs_convertidos_detalle = Column(Text, default='[]')

    sede = relationship("Sede", back_populates="cierres_caja")


class TasaCambio(Base):
    """🌐 GLOBAL - Sin sede_id"""
    __tablename__ = "tasas_cambio"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(DECIMAL(20, 6), nullable=False, default=1.0)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))

    usuario = relationship("Usuario")


class DeudaManual(Base):
    __tablename__ = "deudas_manuales"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    nombre_trabajo = Column(String(200), nullable=False)
    monto_deuda = Column(DECIMAL(12, 2), nullable=False)
    saldo_pendiente = Column(DECIMAL(12, 2), nullable=False)
    monto_pagado = Column(DECIMAL(12, 2), default=0.0)
    estado = Column(String(20), default="pendiente")
    trabajo_convertido_id = Column(Integer, ForeignKey("trabajo.id"), nullable=True)
    es_convertida_a_trabajo = Column(Boolean, default=False)
    fecha_conversion = Column(DateTime, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    observaciones = Column(Text, nullable=True)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    cliente = relationship("Cliente", foreign_keys=[cliente_id])
    creador = relationship("Usuario", foreign_keys=[creado_por])
    trabajo_convertido = relationship("Trabajo", foreign_keys=[trabajo_convertido_id])
    sede = relationship("Sede", back_populates="deudas")


class ItemFactura(Base):
    """🌐 Hereda sede de factura padre - Sin sede_id"""
    __tablename__ = "item_factura"
    id = Column(Integer, primary_key=True, index=True)


# ============================================
# 👷 NÓMINA Y ASISTENCIA
# ============================================

class Prestamo(Base):
    __tablename__ = "prestamo"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id", ondelete="RESTRICT"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha = Column(Date, nullable=False, default="CURRENT_DATE")
    descripcion = Column(String(255))
    pagado = Column(Boolean, default=False)

    empleado = relationship("Empleado")
    sede = relationship("Sede", back_populates="prestamos")


class DeduccionEmpleado(Base):
    __tablename__ = "deduccion_empleado"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    tipo_deduccion = Column(String(20), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    motivo = Column(Text, nullable=False)
    descripcion = Column(Text)
    estado = Column(String(20), default="pendiente")
    fecha_deduccion = Column(DateTime, default=datetime.utcnow)
    fecha_aplicacion = Column(DateTime)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    observaciones = Column(Text)

    empleado = relationship("Empleado")
    trabajo = relationship("Trabajo")
    creador = relationship("Usuario")
    sede = relationship("Sede", back_populates="deducciones")


class PagoSemanal(Base):
    __tablename__ = "pago_semanal"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    fecha_pago = Column(Date, nullable=False)
    semana_inicio = Column(Date, nullable=False)
    semana_fin = Column(Date, nullable=False)
    sueldo_fijo = Column(DECIMAL(10, 2), default=0.0)
    total_comisiones = Column(DECIMAL(10, 2), default=0.0)
    total_prestamos = Column(DECIMAL(10, 2), default=0.0)
    total_deducciones = Column(DECIMAL(10, 2), default=0.0)
    total_neto = Column(DECIMAL(10, 2), nullable=False)
    monto_bs = Column(DECIMAL(15, 2), default=0.0)
    tasa_cambio = Column(DECIMAL(10, 4), default=0.0)
    procesado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_procesamiento = Column(DateTime, default=datetime.utcnow)

    empleado = relationship("Empleado")
    procesador = relationship("Usuario")
    sede = relationship("Sede", back_populates="pagos_semanales")


class CompraEmpleado(Base):
    __tablename__ = "compras_empleado"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=True)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    tipo_producto = Column(String(50), nullable=False)
    descripcion_producto = Column(Text, nullable=False)
    cantidad = Column(Integer, default=1, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    descuento_aplicado = Column(DECIMAL(10, 2), default=0.00)
    total_a_descontar = Column(DECIMAL(10, 2), nullable=False)
    fecha_compra = Column(DateTime, default=datetime.utcnow)
    estado_pago = Column(String(20), default="pendiente")
    observaciones = Column(Text)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    empleado = relationship("Empleado", back_populates="compras")
    trabajo = relationship("Trabajo", foreign_keys=[trabajo_id])
    sede = relationship("Sede", back_populates="compras_empleado")


class Asistencia(Base):
    __tablename__ = "asistencia"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id", ondelete="CASCADE"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    fecha = Column(Date, nullable=False, default=date.today)
    estado = Column(String(20), nullable=False, default="presente")

    empleado = relationship("Empleado", back_populates="asistencias")
    sede = relationship("Sede", back_populates="asistencias")


class ReporteSemanal(Base):
    __tablename__ = "reporte_semanal"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    semana_inicio = Column(Date, nullable=False)
    semana_fin = Column(Date, nullable=False)
    generado_en = Column(DateTime, default=datetime.utcnow)
    datos = Column(JSON)
    archivo_pdf_path = Column(String(255), nullable=True)

    sede = relationship("Sede", back_populates="reportes_semanales")


# ============================================
# 🏗️ ACTIVOS FIJOS
# ============================================

class CategoriaActivoFijo(Base):
    """🌐 GLOBAL - Sin sede_id"""
    __tablename__ = "categoria_activo_fijo"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    vida_util_anios = Column(Integer, nullable=False)
    tasa_depreciacion = Column(Float, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

    activos = relationship("ActivoFijo", back_populates="categoria")


class Departamento(Base):
    """🌐 GLOBAL - Sin sede_id"""
    __tablename__ = "departamento"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    activos = relationship("ActivoFijo", back_populates="departamento")


class ActivoFijo(Base):
    __tablename__ = "activo_fijo"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categoria_activo_fijo.id"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    marca = Column(String(100))
    modelo = Column(String(100))
    numero_serie = Column(String(100), unique=True)
    fecha_adquisicion = Column(Date, nullable=False)
    costo_inicial = Column(DECIMAL(12, 2), nullable=False)
    valor_residual = Column(DECIMAL(12, 2), default=0.00)
    ubicacion = Column(String(200))
    estado = Column(String(20), default="activo")
    empleado_asignado_id = Column(Integer, ForeignKey("empleado.id"))
    departamento_id = Column(Integer, ForeignKey("departamento.id"))
    observaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow)

    categoria = relationship("CategoriaActivoFijo", back_populates="activos")
    empleado_asignado = relationship("Empleado")
    departamento = relationship("Departamento")
    movimientos = relationship("MovimientoActivoFijo", back_populates="activo")
    sede = relationship("Sede", back_populates="activos")


class MovimientoActivoFijo(Base):
    __tablename__ = "movimiento_activo_fijo"

    id = Column(Integer, primary_key=True, index=True)
    activo_id = Column(Integer, ForeignKey("activo_fijo.id"), nullable=False)

    # 🔥 SEDE
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    tipo = Column(String(30), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    empleado_id = Column(Integer, ForeignKey("empleado.id"))
    empleado_asignado_id = Column(Integer, ForeignKey("empleado.id"))
    departamento_id = Column(Integer, ForeignKey("departamento.id"))
    ubicacion_anterior = Column(String(200))
    ubicacion_nueva = Column(String(200))
    motivo = Column(Text, nullable=False)
    observaciones = Column(Text)

    activo = relationship("ActivoFijo", back_populates="movimientos")
    empleado = relationship("Empleado", foreign_keys=[empleado_id])
    departamento = relationship("Departamento")
    sede = relationship("Sede", back_populates="movimientos_activo")


# ============================================
# 🍳 RECETAS DE PRODUCTOS
# ============================================

class RecetaProducto(Base):
    """🌐 GLOBAL - Las recetas son compartidas entre sedes"""
    __tablename__ = "receta_producto"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    categoria = Column(String(50), nullable=True, index=True)
    unidad_medida = Column(String(20), default="unidad")
    precio_sugerido = Column(Float, default=0)
    precio_minimo = Column(Float, default=0)
    descripcion = Column(String(500), default="")
    activo = Column(Boolean, default=True, index=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    materiales = relationship("RecetaMaterial", back_populates="receta", cascade="all, delete-orphan")

    @property
    def costo_total(self):
        return sum(m.costo_total for m in self.materiales)

    @property
    def ganancia_esperada(self):
        return max(0, self.precio_sugerido - self.costo_total)

    @property
    def margen_porcentaje(self):
        if self.precio_sugerido > 0:
            return (self.ganancia_esperada / self.precio_sugerido) * 100
        return 0


class RecetaMaterial(Base):
    """🌐 Hereda de receta global - Sin sede_id"""
    __tablename__ = "receta_material"

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey("receta_producto.id", ondelete="CASCADE"), nullable=False)
    nombre_material = Column(String(100), nullable=False)
    cantidad = Column(Float, default=0)
    unidad = Column(String(20), default="unidad")
    costo_unitario = Column(Float, default=0)
    costo_total = Column(Float, default=0)

    material_inventario_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=True)

    receta = relationship("RecetaProducto", back_populates="materiales")
    material_inventario = relationship("MaterialInventario", foreign_keys=[material_inventario_id])


