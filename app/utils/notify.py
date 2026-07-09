
from datetime import datetime
from app.websocket.manager import notification_manager

async def enviar_notificacion(
    sender_id: int,
    sender_nombre: str,
    sender_rol: str,
    accion: str,
    modulo: str,
    target_nombre: str = None
):
    # Configuración según la acción
    if accion == "crear_trabajo":
        if target_nombre:
            texto = f"{sender_nombre} creó el trabajo: {target_nombre}"
            icono = "✅"
            bgColor = "#D1FAE5"
        else:
            texto = f"{sender_nombre} está creando un trabajo"
            icono = "🔧"
            bgColor = "#E0E7FF"
            
    elif accion == "crear_presupuesto":
        if target_nombre:
            texto = f"{sender_nombre} creó el presupuesto: {target_nombre}"
            icono = "✅"
            bgColor = "#D1FAE5"
        else:
            texto = f"{sender_nombre} está creando un presupuesto"
            icono = "📄"
            bgColor = "#FEF3C7"
            
    elif accion == "crear_factura":
        if target_nombre:
            texto = f"{sender_nombre} creó la factura: {target_nombre}"
            icono = "✅"
            bgColor = "#D1FAE5"
        else:
            texto = f"{sender_nombre} está creando una factura"
            icono = "📃"
            bgColor = "#DBEAFE"
            
    elif accion == "crear_usuario":
        texto = f"{sender_nombre} creó un nuevo usuario: {target_nombre}"
        icono = "👤"
        bgColor = "#D1FAE5"
        
    elif accion == "crear_cliente":
        texto = f"{sender_nombre} agregó un nuevo cliente: {target_nombre}"
        icono = "👥"
        bgColor = "#DBEAFE"
        
    elif accion == "eliminar":
        texto = f"{sender_nombre} eliminó {modulo}: {target_nombre}"
        icono = "🗑️"
        bgColor = "#FEE2E2"
        
    elif accion == "escribiendo_trabajo":
        texto = f"{sender_nombre} está creando un trabajo"
        icono = "✏️"
        bgColor = "#FEF3C7"
        
    elif accion == "escribiendo_presupuesto":
        texto = f"{sender_nombre} está creando un presupuesto"
        icono = "✏️"
        bgColor = "#FEF3C7"
        
    else:
        texto = f"{sender_nombre} realizó una acción en {modulo}"
        icono = "⚡"
        bgColor = "#E0E7FF"
    
    # Ícono según rol
    if sender_rol == "administrador":
        rol_icono = "👑"
    elif sender_rol == "contable":
        rol_icono = "📊"
    else:
        rol_icono = "🔧"
    
    mensaje = {
        "type": "notificacion",
        "notificacion": {
            "accion": accion,
            "modulo": modulo,
            "usuario_actor_nombre": sender_nombre,
            "usuario_actor_rol": sender_rol,
            "rol_icono": rol_icono,
            "target_nombre": target_nombre,
            "texto": texto,
            "icono": icono,
            "bgColor": bgColor,
            "color": "#4f46e5",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    await notification_manager.send_notification(sender_id, sender_nombre, sender_rol, mensaje)


async def enviar_notificacion_escribiendo(
    sender_id: int,
    sender_nombre: str,
    sender_rol: str,
    modulo: str,
    target_nombre: str = None
):
    """Notificación mientras el usuario está escribiendo"""
    
    if modulo == "trabajos":
        accion = "escribiendo_trabajo"
        texto = f"{sender_nombre} está creando un trabajo"
        if target_nombre:
            texto += f": {target_nombre}"
        icono = "✏️"
    elif modulo == "presupuestos":
        accion = "escribiendo_presupuesto"
        texto = f"{sender_nombre} está creando un presupuesto"
        if target_nombre:
            texto += f": {target_nombre}"
        icono = "✏️"
    else:
        accion = "escribiendo"
        texto = f"{sender_nombre} está escribiendo..."
        icono = "✏️"
    
    # Ícono según rol
    if sender_rol == "administrador":
        rol_icono = "👑"
    elif sender_rol == "contable":
        rol_icono = "📊"
    else:
        rol_icono = "🔧"
    
    mensaje = {
        "type": "notificacion",
        "notificacion": {
            "accion": accion,
            "modulo": modulo,
            "usuario_actor_nombre": sender_nombre,
            "usuario_actor_rol": sender_rol,
            "rol_icono": rol_icono,
            "target_nombre": target_nombre,
            "texto": texto,
            "icono": icono,
            "bgColor": "#FEF3C7",
            "color": "#D97706",
            "timestamp": datetime.now().isoformat(),
            "temporal": True
        }
    }
    
    await notification_manager.send_notification(sender_id, sender_nombre, sender_rol, mensaje)
