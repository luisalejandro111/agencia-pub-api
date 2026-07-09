# app/models.py
from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, Date, DateTime, ForeignKey, Float, CheckConstraint, Text, func, Numeric, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date, time
from .database import Base
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum 
from sqlalchemy import Enum as SQLEnum 
from app.database import Base 



class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)  # ← EMAIL OBLIGATORIO
    hashed_password = Column(String(200), nullable=False)
    rol = Column(String(20), nullable=False)  # "administrador" o "operativo" o "contable"
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

     # Agregar la relación con Empleado
    empleado_id = Column(Integer, ForeignKey("empleado.id", ondelete="SET NULL"), nullable=True)
    
    # Relación con Empleado
    empleado = relationship("Empleado", back_populates="usuario")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    tipo_cliente = Column(String(20), nullable=False)  # 'natural' o 'juridico'
    
    # Campos comunes
    nombre_razon_social = Column(String(150), nullable=False)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    notas = Column(Text)
    activo = Column(Boolean, default=True)
    
    # Persona natural
    cedula = Column(String(20))
    primer_nombre = Column(String(50))
    segundo_nombre = Column(String(50))
    primer_apellido = Column(String(50))
    segundo_apellido = Column(String(50))
    
    # Persona jurídica
    rif = Column(String(20))
    representante_legal = Column(String(100))
    telefono_empresa = Column(String(20))
    sitio_web = Column(String(100))
    
    # 🔥 NUEVO: Vínculo con empleado
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=True)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow) 

    # Relaciones
    
    empleado = relationship("Empleado", foreign_keys=[empleado_id])
      
   

class Rol(Base):
    __tablename__ = "rol"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

    # Relaciones
    asignaciones = relationship("Asignacion", back_populates="rol")

from sqlalchemy.orm import relationship

class Empleado(Base):
    __tablename__ = "empleado"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(100), nullable=False)
    tipo_contrato = Column(String(20), nullable=False)
    sueldo_fijo = Column("salario_fijo", DECIMAL(10, 2), default=0.0, nullable=True)
    activo = Column(Boolean, default=True)
    rol_id = Column(Integer, ForeignKey("rol.id", ondelete="SET NULL"))

    # Relaciones
    rol = relationship("Rol")
    asignaciones = relationship("Asignacion", back_populates="empleado")  # ← esta línea es clave
    # 🔥 RELACIÓN CON CLIENTE (opcional, pero útil)
    cliente = relationship("Cliente", back_populates="empleado", uselist=False)
    compras = relationship("CompraEmpleado", back_populates="empleado")

    # NUEVOS CAMPOS PARA ASISTENCIA
    hora_entrada_default = Column(Time, default=time(9, 0))  # 9:00 AM
    hora_salida_default = Column(Time, default=time(18, 0))   # 6:00 PM
    bono_puntualidad_acumulado = Column(DECIMAL(10, 2), default=0.0)
    tiene_acceso_qr = Column(Boolean, default=True)  # Si el empleado puede usar QR

    asistencias = relationship("Asistencia", back_populates="empleado")
    usuario = relationship("Usuario", back_populates="empleado", uselist=False)


class Trabajo(Base):
    __tablename__ = "trabajo"
    
    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nombre_trabajo = Column(String(200), nullable=False)
    monto_total = Column(DECIMAL(10, 2), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    estado = Column(String(50), nullable=False)  
    metros_cuadrados = Column(DECIMAL(8, 2))
    unidades = Column(Integer)
    descripcion = Column(Text, nullable=True)
    prioridad = Column(String(20), default="media")  # baja, media, alta
    #servicio_externo_concepto = Column(String(200), nullable=True)
    monto_total = Column(DECIMAL(12, 2))          # Monto total del trabajo
    monto_pagado_usd = Column(DECIMAL(12, 2), default=0.0)  # Total pagado en USD
    monto_pagado_bs = Column(DECIMAL(15, 2), default=0.0)   # Total pagado en Bs
    porcentaje_pagado = Column(Integer, default=0)
    tasa_cambio_actual = Column(DECIMAL(10, 4))
    metodo_pago = Column(String(50))  # 'efectivo_usd', 'efectivo_bs', etc.
    fecha_pago = Column(DateTime)  
    
    archivos = relationship("ArchivoTrabajo", back_populates="trabajo", cascade="all, delete-orphan")
    servicios_externos = relationship("ServicioExterno", back_populates="trabajo", cascade="all, delete-orphan")

    tipo_trabajo = Column(String(50), default="rotulado_instalacion")  # 'rotulado_instalacion' o 'textil'
    
   

    # Campos financieros
    total_presupuestado = Column(DECIMAL(12, 2))  # Del presupuesto
    monto_pagado = Column(DECIMAL(12, 2), default=0.0)
    porcentaje_pagado = Column(Integer, default=0)

     # Entrega
    entregado = Column(Boolean, default=False)
    fecha_entrega = Column(DateTime, nullable=True)

     # Fechas
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_finalizacion = Column(DateTime, nullable=True)

    
    # Montos en USD (para cálculos precisos)
    monto_total_usd = Column(DECIMAL(12, 2))
    total_materiales_usd = Column(DECIMAL(12, 2), default=0.0)
    total_comisiones_usd = Column(DECIMAL(12, 2), default=0.0)
    servicios_externos_usd = Column(DECIMAL(12, 2), default=0.0)
    ganancia_neta_usd = Column(DECIMAL(12, 2), default=0.0)
    
    # Montos en Bolívares (para mostrar)
    monto_total_bs = Column(DECIMAL(12, 2))
    total_materiales_bs = Column(DECIMAL(12, 2), default=0.0)
    total_comisiones_bs = Column(DECIMAL(12, 2), default=0.0)
    servicios_externos_bs = Column(DECIMAL(12, 2), default=0.0)
    ganancia_neta_bs = Column(DECIMAL(12, 2), default=0.0)
    
    # Tasa de cambio usada
    tasa_cambio = Column(DECIMAL(10, 4))


    # En tu modelo Trabajo
    monto_pagado_usd = Column(DECIMAL(12, 2), default=0.0)      # Monto pagado en USD
    monto_pagado_bs = Column(DECIMAL(12, 2), default=0.0)        # Monto pagado en Bs
    porcentaje_pagado = Column(Integer, default=0)               # Porcentaje actual
    tasa_cambio_actual = Column(DECIMAL(12, 6), default=1.0)     # Tasa al momento del último pago

  
        # Inventario
    materiales_usados = Column(JSON, nullable=True)  # Opcional para registro

    creado_por = Column(Integer, ForeignKey("usuarios.id"))

# Relaciones
    asignaciones = relationship("Asignacion", back_populates="trabajo", cascade="all, delete-orphan")
    

    papel_sublimacion_nombre = Column(String(200), nullable=True)
    papel_sublimacion_cantidad = Column(String(50), nullable=True)


class ServicioExterno(Base):
    __tablename__ = "servicios_externos"
    
    id = Column(Integer, primary_key=True, index=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    concepto = Column(String(200), nullable=False)
    proveedor = Column(String(200), nullable=True)
    costo = Column(DECIMAL(10, 2), nullable=False, default=0.0)
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    # Relación
    trabajo = relationship("Trabajo", back_populates="servicios_externos")

class ArchivoTrabajo(Base):   
    __tablename__ = "archivo_trabajo"
    
    id = Column(Integer, primary_key=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    nombre_guardado = Column(String(255), nullable=False)  # Nombre único en el servidor
    ruta_completa = Column(String(500), nullable=False)
    tipo_mime = Column(String(100), nullable=False)
    tamano_bytes = Column(Integer, nullable=False)
    fecha_subida = Column(DateTime, default=datetime.utcnow)
    descripcion = Column(Text, nullable=True)
    
    # Relación
    trabajo = relationship("Trabajo", back_populates="archivos")

class Asignacion(Base):
    __tablename__ = "asignacion"
    
    id = Column(Integer, primary_key=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)
    rol_id = Column(Integer, ForeignKey("rol.id"), nullable=False)  # ← debe existir
    tipo_comision = Column(String(20), default="porcentaje")
    valor_unitario = Column(DECIMAL(10, 2))
    valor_comision = Column(DECIMAL(8, 2), nullable=False, default=0.0)
    
    # Relaciones
    trabajo = relationship("Trabajo", back_populates="asignaciones")
    empleado = relationship("Empleado", back_populates="asignaciones")
    rol = relationship("Rol", back_populates="asignaciones")  # ← debe existir


class GastoDiario(Base):
    __tablename__ = "gasto_diario"
    
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, default=date.today())
    monto = Column(DECIMAL(10, 2), nullable=False)
    descripcion = Column(String(255))
    categoria_id = Column(Integer, ForeignKey("categoria_gasto.id"), default=4)
    subcategoria_id = Column(Integer, ForeignKey("subcategoria_gasto.id"), default=4)
    empleado_id = Column(Integer, ForeignKey("empleado.id"))
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"))
    
    # Relaciones con back_populates si es necesario
    categoria = relationship("CategoriaGasto", foreign_keys=[categoria_id])
    subcategoria = relationship("SubcategoriaGasto", foreign_keys=[subcategoria_id])

    
class Prestamo(Base):
    __tablename__ = "prestamo"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id", ondelete="RESTRICT"), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    fecha = Column(Date, nullable=False, default="CURRENT_DATE")
    descripcion = Column(String(255))
    pagado = Column(Boolean, default=False)

    # Relación
    empleado = relationship("Empleado")

class TipoTrabajo(Base):
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
    nombre_trabajo = Column(String(200), nullable=False)
    tipo_trabajo_id = Column(Integer, ForeignKey("tipos_trabajo.id"))
    estado = Column(String(20), default="borrador")
    observaciones = Column(Text)
    validez_dias = Column(Integer, default=15)
    total_base = Column(DECIMAL(12, 2)) 
    total_cliente = Column(DECIMAL(12, 2), nullable=False)
    tasa_aplicada = Column(DECIMAL(10, 2)) 
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_envio = Column(DateTime)
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    cliente = relationship("Cliente")
    tipo_trabajo = relationship("TipoTrabajo")
    items_cliente = relationship("ItemPresupuestoCliente", cascade="all, delete-orphan")
    items_internos = relationship("ItemPresupuestoInterno", cascade="all, delete-orphan")
    total_base = Column(DECIMAL(12, 2), nullable=False, default=0.0)
    total_cliente = Column(DECIMAL(12, 2), nullable=False, default=0.0)

class ItemPresupuestoCliente(Base):
    __tablename__ = "items_presupuesto_cliente"
    
    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    concepto = Column(String(200), nullable=False)  # "Diseño y maquetación"
    monto = Column(DECIMAL(10, 2), nullable=False)   # $50.00
    orden = Column(Integer, default=0)

class ItemPresupuestoInterno(Base):
    __tablename__ = "items_presupuesto_interno"
    
    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    tipo_item = Column(String(30), nullable=False)  # "material", "mano_obra", "logistica"
    descripcion = Column(String(200), nullable=False)  # "Vinilo premium 3m²"
    costo = Column(DECIMAL(10, 2), nullable=False)   # $45.00
    orden = Column(Integer, default=0)

class ItemPresupuesto(Base):
    __tablename__ = "items_presupuesto"
    
    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"))
    concepto = Column(String(200), nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    cantidad = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    unidad_medida = Column(String(20), nullable=False)

class InventarioMaterial(Base):
    __tablename__ = "inventario_material"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True)
    cantidad_disponible = Column(DECIMAL(10, 2), default=0.0)

class MaterialUsado(Base):
    __tablename__ = "material_usado"
    
    id = Column(Integer, primary_key=True)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=True)  # Opcional
    concepto = Column(String(200), nullable=True)  # Para conceptos libres
    cantidad_usada = Column(DECIMAL(10, 2), nullable=False)
    costo_unitario = Column(DECIMAL(12, 2), nullable=True)

    material = relationship("MaterialInventario", back_populates="usos")


class CategoriaInventario(Base):
    __tablename__ = "categoria_inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    # Relación con materiales
    materiales = relationship("MaterialInventario", back_populates="categoria")

class Proveedor(Base):
    __tablename__ = "proveedor"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    contacto = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(String(255))
    ruc = Column(String(20))  # Opcional para facturación
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    # Relación con entradas de inventario
    entradas = relationship("EntradaInventario", back_populates="proveedor")

class MaterialInventario(Base):
    __tablename__ = "material_inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)  # Código interno único
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categoria_inventario.id"), nullable=False)
    unidad_medida = Column(String(20), nullable=False)  # m², unidades, litros, rollos, kg, etc.
    m2_por_unidad = Column(Float, default=1.0)
    stock_actual = Column(Float, default=0.0, nullable=False)
    stock_minimo = Column(Float, default=0.0, nullable=False)
    precio_compra = Column(DECIMAL(10, 2), default=0.00)  # Precio promedio de compra
    ubicacion = Column(String(100))  # Almacén, estante, código de ubicación
    observaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activo = Column(Boolean, default=True)
    precio_venta = Column(DECIMAL(10, 2), default=0.00)
    
    # Relaciones
    categoria = relationship("CategoriaInventario", back_populates="materiales")
    movimientos = relationship("MovimientoInventario", back_populates="material")
    entradas = relationship("EntradaInventario", back_populates="material")
    salidas = relationship("SalidaMaterial", back_populates="material")
    usos = relationship("MaterialUsado", back_populates="material")

class EntradaInventario(Base):
    __tablename__ = "entrada_inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"))
    cantidad = Column(Float, nullable=False)
    precio_compra = Column(DECIMAL(10, 2), nullable=False)
    numero_factura = Column(String(50))
    fecha_entrada = Column(DateTime, default=datetime.utcnow)
    observaciones = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Relaciones
    material = relationship("MaterialInventario", back_populates="entradas")
    proveedor = relationship("Proveedor", back_populates="entradas")
   

class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material_inventario.id"), nullable=False)
    tipo = Column(String(20), nullable=False)  # 'entrada', 'salida', 'ajuste'
    cantidad = Column(Float, nullable=False)
    motivo = Column(String(200), nullable=False)  # Compra, uso_trabajo, ajuste_stock, etc.
    referencia = Column(String(100))  # ID trabajo, número de factura, etc.
    fecha = Column(DateTime, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    observaciones = Column(Text)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"))
    
    # Relaciones
    material = relationship("MaterialInventario", back_populates="movimientos")
    trabajo = relationship("Trabajo")
    usuario = relationship("Usuario")

class CategoriaActivoFijo(Base):
    __tablename__ = "categoria_activo_fijo"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    vida_util_anios = Column(Integer, nullable=False)  # Para cálculo de depreciación
    tasa_depreciacion = Column(Float, nullable=False)  # Porcentaje anual
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    # Relación
    activos = relationship("ActivoFijo", back_populates="categoria")

class ActivoFijo(Base):
    __tablename__ = "activo_fijo"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey("categoria_activo_fijo.id"), nullable=False)
    marca = Column(String(100))
    modelo = Column(String(100))
    numero_serie = Column(String(100), unique=True)
    fecha_adquisicion = Column(Date, nullable=False)
    costo_inicial = Column(DECIMAL(12, 2), nullable=False)
    valor_residual = Column(DECIMAL(12, 2), default=0.00)
    ubicacion = Column(String(200))
    estado = Column(String(20), default="activo")  # activo, inactivo, dado_baja, en_reparacion
    empleado_asignado_id = Column(Integer, ForeignKey("empleado.id"))
    departamento_id = Column(Integer, ForeignKey("departamento.id"))
    observaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    categoria = relationship("CategoriaActivoFijo", back_populates="activos")
    empleado_asignado = relationship("Empleado")
    departamento = relationship("Departamento")
    movimientos = relationship("MovimientoActivoFijo", back_populates="activo")

class MovimientoActivoFijo(Base):
    __tablename__ = "movimiento_activo_fijo"
    
    id = Column(Integer, primary_key=True, index=True)
    activo_id = Column(Integer, ForeignKey("activo_fijo.id"), nullable=False)
    tipo = Column(String(30), nullable=False)  # asignacion, desasignacion, traslado, baja, reparacion
    fecha = Column(DateTime, default=datetime.utcnow)
    empleado_id = Column(Integer, ForeignKey("empleado.id"))  # Empleado que realiza el movimiento
    empleado_asignado_id = Column(Integer, ForeignKey("empleado.id"))  # Nuevo empleado asignado
    departamento_id = Column(Integer, ForeignKey("departamento.id"))
    ubicacion_anterior = Column(String(200))
    ubicacion_nueva = Column(String(200))
    motivo = Column(Text, nullable=False)
    observaciones = Column(Text)
    
    # Relaciones
    activo = relationship("ActivoFijo", back_populates="movimientos")
    empleado = relationship("Empleado", foreign_keys=[empleado_id])
    empleado_asignado = relationship("Empleado", foreign_keys=[empleado_asignado_id])
    departamento = relationship("Departamento")

class Departamento(Base):
    __tablename__ = "departamento"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones (opcional, si las necesitas)
    activos = relationship("ActivoFijo", back_populates="departamento")

class DeduccionEmpleado(Base):
    __tablename__ = "deduccion_empleado"
    
    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=False)
    tipo_deduccion = Column(String(20), nullable=False)  # 'fijo', 'porcentaje', 'monto_total'
    monto = Column(DECIMAL(10, 2), nullable=False)  # Monto fijo o porcentaje
    motivo = Column(Text, nullable=False)
    descripcion = Column(Text)
    estado = Column(String(20), default="pendiente")  # pendiente, aplicada, cancelada
    fecha_deduccion = Column(DateTime, default=datetime.utcnow)
    fecha_aplicacion = Column(DateTime)  # Cuando se aplica al salario
    creado_por = Column(Integer, ForeignKey("usuarios.id"))  # Quién registró la deducción
    observaciones = Column(Text)
    
    # Relaciones
    empleado = relationship("Empleado")
    trabajo = relationship("Trabajo")
    creador = relationship("Usuario")

class SalidaMaterial(Base):
    __tablename__ = "salida_material"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("material_inventario.id"))
    cantidad = Column(DECIMAL(10, 2))
    tipo_salida = Column(String(50))
    motivo = Column(Text)
    referencia_id = Column(Integer)  # ID del trabajo
    tipo_referencia = Column(String(50))  # 'trabajo'
    creado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_salida = Column(DateTime, default=datetime.utcnow)

    material = relationship("MaterialInventario", back_populates="salidas")


class IngresoDiario(Base):
    __tablename__ = 'ingreso_diario'
    
    id = Column(Integer, primary_key=True)
    cierre_caja_id = Column(Integer, ForeignKey('cierre_caja.id'), nullable=False)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    trabajo_id = Column(Integer, ForeignKey('trabajo.id'))
    presupuesto_id = Column(Integer, ForeignKey('presupuestos.id'))
    
    concepto = Column(String(200), nullable=False)
    monto_usd = Column(DECIMAL(10, 2), nullable=False)
    monto_bs = Column(DECIMAL(15, 2), nullable=False)
    metodo_pago = Column(String(50), nullable=False)  # 'efectivo', 'transferencia', 'pago_movil', 'tarjeta'
    referencia = Column(String(100))  # número de transacción, referencia bancaria
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    observaciones = Column(Text)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    cierre_caja = relationship("CierreCaja")
    cliente = relationship("Cliente")
    trabajo = relationship("Trabajo")
    presupuesto = relationship("Presupuesto")



class PagoSemanal(Base):
    __tablename__ = "pago_semanal"
    
    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)
    fecha_pago = Column(Date, nullable=False)
    semana_inicio = Column(Date, nullable=False)
    semana_fin = Column(Date, nullable=False)
    
    sueldo_fijo = Column(DECIMAL(10, 2), default=0.0)
    total_comisiones = Column(DECIMAL(10, 2), default=0.0)
    total_prestamos = Column(DECIMAL(10, 2), default=0.0)
    total_deducciones = Column(DECIMAL(10, 2), default=0.0)
    total_neto = Column(DECIMAL(10, 2), nullable=False)
    
    # ✅ NUEVO: Campo para monto en Bolívares
    monto_bs = Column(DECIMAL(15, 2), default=0.0)
    
    # ✅ NUEVO: Guardar la tasa usada para auditoría
    tasa_cambio = Column(DECIMAL(10, 4), default=0.0)
    
    procesado_por = Column(Integer, ForeignKey("usuarios.id"))
    fecha_procesamiento = Column(DateTime, default=datetime.utcnow)
    
    empleado = relationship("Empleado")
    procesador = relationship("Usuario")


class CategoriaGasto(Base):
    __tablename__ = "categoria_gasto"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(String(200))
    orden = Column(Integer, default=0)
    activa = Column(Boolean, default=True)

class SubcategoriaGasto(Base):
    __tablename__ = "subcategoria_gasto"
    
    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categoria_gasto.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(200))
    orden = Column(Integer, default=0)
    activa = Column(Boolean, default=True)

    categoria = relationship("CategoriaGasto")

class CierreCaja(Base):
    __tablename__ = "cierre_caja"
    
    id = Column(Integer, primary_key=True)
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
    pagos_usd_directos = Column(Float, default=0)           # Total de pagos en USD directos
    pagos_bs_convertidos_usd = Column(Float, default=0)     # Total de pagos en Bs convertidos a USD
    pagos_bs_convertidos_detalle = Column(Text, default='[]')



class CompraEmpleado(Base):
    __tablename__ = "compras_empleado"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id"), nullable=False)  # Empleado que compra
    trabajo_id = Column(Integer, ForeignKey("trabajo.id"), nullable=True)  # Opcional: si se compra en contexto de trabajo
    tipo_producto = Column(String(50), nullable=False)  # Ej: "jersey", "trabajo", "uniforme"
    descripcion_producto = Column(Text, nullable=False)
    cantidad = Column(Integer, default=1, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    descuento_aplicado = Column(DECIMAL(10, 2), default=0.00)
    total_a_descontar = Column(DECIMAL(10, 2), nullable=False)  # Monto final a restar del sueldo
    fecha_compra = Column(DateTime, default=datetime.utcnow)
    estado_pago = Column(String(20), default="pendiente")  # pendiente, descontado, anulado
    observaciones = Column(Text)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # ✅ RELACIONES CORRECTAS (sin "compras_al_negocio")
    empleado = relationship("Empleado", back_populates="compras")  # back_populates debe coincidir
    trabajo = relationship("Trabajo", foreign_keys=[trabajo_id])


class ReporteSemanal(Base):
    __tablename__ = "reporte_semanal"

    id = Column(Integer, primary_key=True, index=True)
    semana_inicio = Column(Date, nullable=False)
    semana_fin = Column(Date, nullable=False)
    generado_en = Column(DateTime, default=datetime.utcnow)
    datos = Column(JSON)
    
    # ✅ AGREGAR ESTA LÍNEA SI NO ESTÁ
    archivo_pdf_path = Column(String(255), nullable=True)

   


class Asistencia(Base):
    __tablename__ = "asistencia"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("empleado.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(Date, nullable=False, default=date.today)
    estado = Column(String(20), nullable=False, default="presente")  # presente, ausente

    # Relación
    empleado = relationship("Empleado", back_populates="asistencias")

class TrabajoMaterialTextil(Base):
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
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    trabajo = relationship("Trabajo", foreign_keys=[trabajo_id])


class DeudaManual(Base):
    """Deudas manuales cargadas para clientes existentes"""
    __tablename__ = "deudas_manuales"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    nombre_trabajo = Column(String(200), nullable=False)
    monto_deuda = Column(DECIMAL(12, 2), nullable=False)
    saldo_pendiente = Column(DECIMAL(12, 2), nullable=False)
    monto_pagado = Column(DECIMAL(12, 2), default=0.0)
    estado = Column(String(20), default="pendiente")  # pendiente, parcial, pagado
    
    # 🔥 NUEVO: Para rastrear si se convierte en trabajo formal
    trabajo_convertido_id = Column(Integer, ForeignKey("trabajo.id"), nullable=True)
    es_convertida_a_trabajo = Column(Boolean, default=False)
    fecha_conversion = Column(DateTime, nullable=True)
    
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    observaciones = Column(Text, nullable=True)
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Relaciones
    cliente = relationship("Cliente", foreign_keys=[cliente_id])
    creador = relationship("Usuario", foreign_keys=[creado_por])
    trabajo_convertido = relationship("Trabajo", foreign_keys=[trabajo_convertido_id])


class TasaCambio(Base):
    __tablename__ = "tasas_cambio"
    
    id = Column(Integer, primary_key=True, index=True)
    valor = Column(DECIMAL(20, 6), nullable=False, default=1.0)  # ← COLUMNA 'valor'
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"))
    
    usuario = relationship("Usuario")

class ItemFactura(Base):
    __tablename__ = "item_factura"
    id = Column(Integer, primary_key=True, index=True)



