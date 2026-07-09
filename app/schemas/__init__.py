# app/schemas/__init__.py
"""
Este módulo contiene todos los esquemas Pydantic para validación y serialización.
"""

# --- Esquemas de Usuario ---
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)

# --- Esquemas de Rol ---
from app.schemas.rol import (
    RolBase,
    RolCreate,
    RolUpdate,
    Rol,
    RolResponse,
)

# --- Esquemas de Empleado ---
from app.schemas.empleado import (
    EmpleadoBase,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResponse,
    Empleado,
)

# --- Esquemas de Cliente ---
from app.schemas.cliente import (
    ClienteBase,
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
)

# --- Esquemas de Trabajo ---
from app.schemas.trabajo import (
    TrabajoBase,
    TrabajoCreate,
    TrabajoUpdate,
    TrabajoResponse,
    Trabajo,
)

# --- Esquemas de Asignacion ---
from app.schemas.asignacion import (
    AsignacionBase,
    AsignacionCreate,
    AsignacionUpdate,
    AsignacionResponse,
)

# --- Esquemas de Gasto ---
from app.schemas.gasto import (
    GastoDiarioBase,
    GastoDiarioCreate,
    GastoDiarioUpdate,
    GastoDiarioResponse,
    GastoDiario,
)

# --- Esquemas de Deudas ---
from app.schemas.deudas import (
    DeudaManualCreate,
    DeudaManualUpdate,
    DeudaManualResponse,
    DeudorPendienteResponse,
    ListadoDeudoresResponse,
    ResumenDeudorResponse,
    ConvertirDeudaATrabajo,
)

# Exportar todos los esquemas
__all__ = [
    # Usuario
    "UsuarioCreate",
    "UsuarioResponse",
    "UsuarioUpdate",
    # Rol
    "RolBase",
    "RolCreate",
    "RolUpdate",
    "Rol",
    "RolResponse",
    # Empleado
    "EmpleadoBase",
    "EmpleadoCreate",
    "EmpleadoUpdate",
    "EmpleadoResponse",
    "Empleado",
    # Cliente
    "ClienteBase",
    "ClienteCreate",
    "ClienteUpdate",
    "ClienteResponse",
    # Trabajo
    "TrabajoBase",
    "TrabajoCreate",
    "TrabajoUpdate",
    "TrabajoResponse",
    "Trabajo",
    # Asignacion
    "AsignacionBase",
    "AsignacionCreate",
    "AsignacionUpdate",
    "AsignacionResponse",
    # Gasto
    "GastoDiarioBase",
    "GastoDiarioCreate",
    "GastoDiarioUpdate",
    "GastoDiarioResponse",
    "GastoDiario",
    # Deudas
    "DeudaManualCreate",
    "DeudaManualUpdate",
    "DeudaManualResponse",
    "DeudorPendienteResponse",
    "ListadoDeudoresResponse",
    "ResumenDeudorResponse",
    "ConvertirDeudaATrabajo",
]