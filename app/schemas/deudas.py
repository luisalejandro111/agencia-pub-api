# app/schemas/deudas.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Literal


class DeudaManualCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    nombre_trabajo: str = Field(..., min_length=3, max_length=200)
    monto_deuda: Decimal = Field(..., gt=0, decimal_places=2)
    observaciones: Optional[str] = Field(None, max_length=500)
    
    @field_validator('nombre_trabajo')
    @classmethod
    def validate_nombre_trabajo(cls, v):
        if not v.strip():
            raise ValueError('El nombre del trabajo no puede estar vacío')
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cliente_id": 15,
                "nombre_trabajo": "Ajuste de lona - Publicidad exterior",
                "monto_deuda": 350.00,
                "observaciones": "Cliente solicitó pago a 30 días"
            }
        }
    )


class DeudaManualUpdate(BaseModel):
    monto_pago: Decimal = Field(..., gt=0, decimal_places=2)


class DeudaManualResponse(BaseModel):
    id: int
    cliente_id: int
    nombre_trabajo: str
    monto_deuda: Decimal
    saldo_pendiente: Decimal
    monto_pagado: Decimal
    estado: str
    fecha_registro: datetime
    observaciones: Optional[str] = None
    es_convertida_a_trabajo: bool = False
    trabajo_convertido_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeudorPendienteResponse(BaseModel):
    cliente_id: int
    cliente_nombre: str
    concepto: str
    monto_total: Decimal
    monto_pagado: Decimal
    saldo_pendiente: Decimal
    fecha: datetime
    origen: Literal['trabajo', 'manual']
    trabajo_id: Optional[int] = None
    deuda_manual_id: Optional[int] = None
    porcentaje_pagado: Optional[int] = None
    estado_deuda: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ListadoDeudoresResponse(BaseModel):
    total_registros: int
    total_clientes_unicos: int
    total_adeudado: Decimal = Decimal('0')
    deudores: List[DeudorPendienteResponse]
    resumen_por_origen: dict = {"trabajos": 0, "manuales": 0}


class ResumenDeudorResponse(BaseModel):
    cliente_id: int
    cliente_nombre: str
    total_deuda: Decimal
    total_pagado: Decimal
    saldo_total: Decimal
    cantidad_deudas: int
    deudas_trabajos: int = 0
    deudas_manuales: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ConvertirDeudaATrabajo(BaseModel):
    trabajo_id: int = Field(..., gt=0)
    fecha_inicio: Optional[datetime] = None