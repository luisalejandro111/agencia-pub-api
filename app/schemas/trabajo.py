# app/schemas/trabajo.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class TrabajoBase(BaseModel):
    cliente_id: int
    nombre_trabajo: str = Field(..., min_length=3, max_length=200)
    monto_total: Decimal = Field(..., decimal_places=2, gt=0)
    fecha_inicio: date
    estado: str = Field(..., description="Ej: pendiente, en_progreso, completado")
    tipo_trabajo: str = "rotulado_instalacion"
    descripcion: Optional[str] = None
    prioridad: str = "media"
    metros_cuadrados: Optional[Decimal] = None
    unidades: Optional[int] = None
    tasa_cambio: Optional[Decimal] = None
    presupuesto_id: Optional[int] = None


class TrabajoCreate(TrabajoBase):
    pass


class TrabajoUpdate(BaseModel):
    nombre_trabajo: Optional[str] = None
    monto_total: Optional[Decimal] = None
    estado: Optional[str] = None
    descripcion: Optional[str] = None
    prioridad: Optional[str] = None
    metros_cuadrados: Optional[Decimal] = None
    unidades: Optional[int] = None
    entregado: Optional[bool] = None
    fecha_entrega: Optional[datetime] = None
    fecha_finalizacion: Optional[datetime] = None


class Trabajo(TrabajoBase):  # ← AGREGAR ESTA CLASE
    id: int
    monto_pagado: Decimal = Decimal('0.00')
    monto_pagado_usd: Decimal = Decimal('0.00')
    monto_pagado_bs: Decimal = Decimal('0.00')
    porcentaje_pagado: int = 0
    entregado: bool = False
    fecha_creacion: datetime
    creado_por: Optional[int] = None
    
    class Config:
        from_attributes = True


# Alias para consistencia
TrabajoResponse = Trabajo