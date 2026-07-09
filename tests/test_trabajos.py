import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import Trabajo, Cliente

@pytest.mark.asyncio
async def test_crear_trabajo(authenticated_client: AsyncClient, db_session):
    """Probar creación de trabajo"""
    from tests.factories import ClienteFactory
    
    # Crear cliente primero
    cliente = ClienteFactory()
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)
    
    form_data = {
        "cliente_id": cliente.id,
        "nombre_trabajo": "Trabajo de Prueba",
        "monto_total": "1000.00",
        "estado": "pendiente",
        "fecha_inicio": "2024-01-01",
        "metodo_pago": "efectivo_usd",
        "tipo_trabajo": "rotulado_instalacion"
    }
    
    response = await authenticated_client.post(
        "/trabajos",
        data=form_data,
        follow_redirects=True
    )
    
    assert response.status_code == 200
    
    # Verificar que se creó
    trabajos = await db_session.execute(select(Trabajo))
    trabajo = trabajos.scalars().first()
    assert trabajo is not None
    assert trabajo.nombre_trabajo == "Trabajo de Prueba"

@pytest.mark.asyncio
async def test_registrar_pago_trabajo(authenticated_client: AsyncClient, db_session):
    """Probar registro de pago de trabajo"""
    from tests.factories import TrabajoFactory, ClienteFactory
    
    cliente = ClienteFactory()
    db_session.add(cliente)
    await db_session.commit()
    
    trabajo = TrabajoFactory(
        cliente_id=cliente.id,
        creado_por=1,
        monto_total=1000.0,
        porcentaje_pagado=0,
        estado="pendiente"
    )
    db_session.add(trabajo)
    await db_session.commit()
    
    form_data = {
        "monto_usd": "500.00",
        "tasa_actual": "36.50",
        "metodo_pago": "efectivo_usd",
        "fecha_pago": "2024-01-01T12:00"
    }
    
    response = await authenticated_client.post(
        f"/trabajos/{trabajo.id}/registrar-pago",
        data=form_data,
        follow_redirects=True
    )
    
    assert response.status_code == 200
    await db_session.refresh(trabajo)
    assert trabajo.porcentaje_pagado >= 50