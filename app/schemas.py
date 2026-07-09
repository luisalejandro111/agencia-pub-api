# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# === ROL ===
class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass

class Rol(RolBase):
    id: int

    class Config:
        from_attributes = True

# === EMPLEADO ===
class EmpleadoBase(BaseModel):
    nombre_completo: str
    tipo_contrato: str = Field(..., pattern="^(fijo|comision)$")
    salario_fijo: Optional[float] = None
    activo: bool = True

class EmpleadoCreate(EmpleadoBase):
    pass

class Empleado(EmpleadoBase):
    id: int

    class Config:
        from_attributes = True

# === TRABAJO ===
class TrabajoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    monto_total: float
    fecha_inicio: date
    estado: str = "pendiente"

class TrabajoCreate(TrabajoBase):
    pass

class Trabajo(TrabajoBase):
    id: int

    class Config:
        from_attributes = True


# === ASIGNACIÓN DE EMPLEADO A ROL EN TRABAJO ===
class AsignacionCreate(BaseModel):
    empleado_id: int
    rol_id: int

# === ESQUEMA COMPLETO PARA CREAR TRABAJO CON COMISIONES Y ASIGNACIONES ===
class TrabajoCompletoCreate(BaseModel):
    nombre: str
    monto_total: float
    fecha_inicio: date
    estado: str = "pendiente"
    tipo_trabajo: Optional[str] = None
    metros_cuadrados: Optional[float] = None
    

    # === GASTO DIARIO ===
class GastoDiarioBase(BaseModel):
    fecha: date
    monto: float
    descripcion: Optional[str] = None
    categoria: Optional[str] = None

class GastoDiarioCreate(GastoDiarioBase):
    pass

class GastoDiario(GastoDiarioBase):
    id: int

    class Config:
        from_attributes = True


      # === USUARIO ===
class UsuarioBase(BaseModel):
    nombre: str
    email: str

class UsuarioCreate(UsuarioBase):
    password: str
    rol: str = Field(..., pattern="^(admin|operativo)$")

class Usuario(UsuarioBase):
    id: int
    rol: str

    class Config:
        from_attributes = True  


       # === REPORTE SEMANAL ===
class ReporteSemanalBase(BaseModel):
    semana_inicio: date
    semana_fin: date
    total_comisiones: float
    total_gastos: float
    trabajos_finalizados: int
    comisiones_detalle: list[dict]

class ReporteSemanalCreate(BaseModel):
    semana_inicio: date
    semana_fin: date 

class PrestamoBase(BaseModel):
    empleado_id: int
    monto: float
    descripcion: Optional[str] = None
    semana_inicio: date
    semana_fin: date

class PrestamoCreate(PrestamoBase):
    pass

class Prestamo(PrestamoBase):
    id: int

class Config:
        from_attributes = True 