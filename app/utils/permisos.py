# ============================================
# PERMISOS POR ROL - QUÉ MÓDULOS PUEDE VER CADA UNO
# ============================================

MODULOS_POR_ROL = {
    "administrador": [
        "clientes", "presupuestos", "trabajos", "facturas", 
        "inventario", "activos_fijos", "empleados", "compras_empleados",
        "roles", "deducciones", "prestamos", "finanzas_gastos", 
        "caja_diaria", "cuentas_cobrar", "pagos_empleados", "pagos_pendientes",
        "reportes", "usuarios"  # ← Solo administrador puede ver usuarios
    ],
   
    
    "operativo": [
        "clientes", "presupuestos", "trabajos",
        "empleados", "compras_empleados",
        "deducciones", "prestamos", "finanzas_gastos",
        "caja_diaria", "cuentas_cobrar", "tasas-cambio" 
        
        # ❌ NO tiene "usuarios"
        
    ]
}

# ============================================
# JERARQUÍA DE NOTIFICACIONES - QUIÉN VE LAS ACCIONES DE QUIÉN
# ============================================
# Reglas:
# - administrador: VE todo (todos los roles)
# - contable: VE a operativo y a sí mismo (NO ve a administrador)
# - operativo: SOLO ve sus propias acciones

NOTIFICACIONES_POR_ROL = {
    "administrador": {
        "puede_ver": ["administrador", "contable", "operativo"],  # Ve a todos
        "recibe_notificaciones": True
    },
    "contable": {
        "puede_ver": ["contable", "operativo"],  # Ve a contables y operativos
        "recibe_notificaciones": True
    },
    "operativo": {
        "puede_ver": ["operativo"],  # Solo se ve a sí mismo
        "recibe_notificaciones": False  # No recibe notificaciones de otros
    }
}

def usuario_puede_ver_modulo(rol: str, modulo: str) -> bool:
    """Verifica si un rol puede acceder a un módulo"""
    return modulo in MODULOS_POR_ROL.get(rol, [])

def usuario_puede_ver_notificacion(
    rol_emisor: str, 
    rol_receptor: str,
    es_misma_persona: bool = False
) -> bool:
    """Verifica si el receptor puede ver la notificación del emisor"""
    if es_misma_persona:
        return True  # Siempre ver sus propias acciones
    
    roles_permitidos = NOTIFICACIONES_POR_ROL.get(rol_receptor, {}).get("puede_ver", [])
    return rol_emisor in roles_permitidos

def obtener_modulos_por_rol(rol: str) -> list:
    """Retorna la lista de módulos que puede ver un rol"""
    return MODULOS_POR_ROL.get(rol, [])