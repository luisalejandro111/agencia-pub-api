# app/schemas/asignacion.py
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class AsignacionBase(BaseModel):
    trabajo_id: int
    empleado_id: int
    rol_id: int
    tipo_comision: str = "porcentaje"  # 'porcentaje' o 'fijo'
    valor_unitario: Optional[Decimal] = None
    valor_comision: Decimal = Decimal('0.00')


class AsignacionCreate(AsignacionBase):
    pass


class AsignacionUpdate(BaseModel):
    tipo_comision: Optional[str] = None
    valor_unitario: Optional[Decimal] = None
    valor_comision: Optional[Decimal] = None
    rol_id: Optional[int] = None


class AsignacionResponse(AsignacionBase):
    id: int
    
    class Config:
        from_attributes = True