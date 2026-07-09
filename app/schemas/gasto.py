# app/schemas/gasto.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class GastoDiarioBase(BaseModel):
    fecha: date
    monto: Decimal
    descripcion: str
    categoria_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    empleado_id: Optional[int] = None
    trabajo_id: Optional[int] = None


class GastoDiarioCreate(GastoDiarioBase):
    pass


class GastoDiarioUpdate(BaseModel):
    fecha: Optional[date] = None
    monto: Optional[Decimal] = None
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    empleado_id: Optional[int] = None
    trabajo_id: Optional[int] = None


class GastoDiarioResponse(GastoDiarioBase):
    id: int
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Alias para compatibilidad
GastoDiario = GastoDiarioResponse