from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UsuarioCreate(BaseModel):
    nombre: str
    username: str
    email: EmailStr
    password: str
    rol: str  # "administrador", "contable", "operativo"

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    username: str
    email: str
    rol: str
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None