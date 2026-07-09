# app/schemas/rol.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RolBase(BaseModel):
    nombre: str


class RolCreate(RolBase):
    pass


class RolUpdate(BaseModel):
    nombre: Optional[str] = None


# ✅ AGREGAR ESTA CLASE
class Rol(RolBase):
    id: int
    fecha_creacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# También podemos mantener RolResponse como alias
RolResponse = Rol