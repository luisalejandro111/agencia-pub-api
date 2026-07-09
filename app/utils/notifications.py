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
    # Configuración visual
    if accion == "crear_trabajo":
        icono = "🔧" if not target_nombre else "✅"
        texto = f"{sender_nombre} está creando un trabajo"
        if target_nombre:
            texto = f"{sender_nombre} creó el trabajo: {target_nombre}"
        bgColor = "#D1FAE5" if target_nombre else "#E0E7FF"
    elif accion == "crear_usuario":
        icono = "👤"
        texto = f"{sender_nombre} creó un usuario: {target_nombre}"
        bgColor = "#D1FAE5"
    else:
        icono = "⚡"
        texto = f"{sender_nombre} realizó una acción en {modulo}"
        bgColor = "#E0E7FF"
    
    # Ícono por rol
    rol_icono = "👑" if sender_rol == "administrador" else "📊" if sender_rol == "contable" else "🔧"
    
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
