# app/schemas/empleado.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, time
from decimal import Decimal


class EmpleadoBase(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=100)
    tipo_contrato: str = Field(..., description="Ej: fijo, temporal, por proyecto")
    salario_fijo: Optional[Decimal] = Field(None, decimal_places=2)
    activo: bool = True
    rol_id: Optional[int] = None
    hora_entrada_default: Optional[time] = time(9, 0)
    hora_salida_default: Optional[time] = time(18, 0)
    bono_puntualidad_acumulado: Optional[Decimal] = Decimal('0.00')
    tiene_acceso_qr: bool = True


class EmpleadoCreate(EmpleadoBase):
    pass


class EmpleadoUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    tipo_contrato: Optional[str] = None
    salario_fijo: Optional[Decimal] = None
    activo: Optional[bool] = None
    rol_id: Optional[int] = None
    hora_entrada_default: Optional[time] = None
    hora_salida_default: Optional[time] = None
    bono_puntualidad_acumulado: Optional[Decimal] = None
    tiene_acceso_qr: Optional[bool] = None


class Empleado(EmpleadoBase):  # ← AGREGAR ESTA CLASE
    id: int
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Alias para consistencia
EmpleadoResponse = Empleado