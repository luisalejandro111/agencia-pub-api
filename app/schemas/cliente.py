# app/schemas/cliente.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class ClienteBase(BaseModel):
    tipo_cliente: str = Field(..., description="'natural' o 'juridico'")
    nombre_razon_social: str = Field(..., min_length=3, max_length=150)
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    activo: bool = True


class ClienteCreate(ClienteBase):
    # Persona natural
    cedula: Optional[str] = None
    primer_nombre: Optional[str] = None
    segundo_nombre: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = None
    # Persona jurídica
    rif: Optional[str] = None
    representante_legal: Optional[str] = None
    telefono_empresa: Optional[str] = None
    sitio_web: Optional[str] = None
    empleado_id: Optional[int] = None


class ClienteUpdate(BaseModel):
    nombre_razon_social: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None
    cedula: Optional[str] = None
    primer_nombre: Optional[str] = None
    segundo_nombre: Optional[str] = None
    primer_apellido: Optional[str] = None
    segundo_apellido: Optional[str] = None
    rif: Optional[str] = None
    representante_legal: Optional[str] = None
    telefono_empresa: Optional[str] = None
    sitio_web: Optional[str] = None
    empleado_id: Optional[int] = None


class ClienteResponse(ClienteBase):
    id: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True