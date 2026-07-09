from sqlalchemy.orm import Session
from app.models.notificacion import Notificacion
from app.websocket.manager import manager  # Lo crearemos después
import json
from datetime import datetime

def crear_y_enviar_notificacion(
    db: Session,
    accion: str,
    modulo: str,
    usuario_actor_id: int,
    usuario_actor_nombre: str,
    usuario_actor_rol: str,
    target_nombre: str = None,
    target_id: int = None,
    usuario_destino_id: int = None
):
    """Guarda notificación en BD y la envía por WebSocket"""
    
    # 1. Guardar en base de datos
    notificacion_db = Notificacion(
        accion=accion,
        modulo=modulo,
        usuario_actor_id=usuario_actor_id,
        usuario_destino_id=usuario_destino_id,
        target_nombre=target_nombre,
        target_id=target_id,
        leido=0
    )
    db.add(notificacion_db)
    db.commit()
    db.refresh(notificacion_db)
    
    # 2. Preparar mensaje para WebSocket
    mensaje = {
        "type": "notificacion",
        "notificacion": {
            "id": notificacion_db.id,
            "accion": accion,
            "modulo": modulo,
            "usuario_actor_id": usuario_actor_id,
            "usuario_actor_nombre": usuario_actor_nombre,
            "usuario_actor_rol": usuario_actor_rol,
            "target_nombre": target_nombre,
            "target_id": target_id,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # 3. Enviar por WebSocket
    import asyncio
    if usuario_destino_id:
        # Enviar a usuario específico
        asyncio.create_task(manager.send_to_user(usuario_destino_id, mensaje))
    else:
        # Enviar a todos los usuarios conectados
        asyncio.create_task(manager.broadcast_to_all(mensaje))
    
    return notificacion_db