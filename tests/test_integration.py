import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import Cliente, Trabajo

@pytest.mark.asyncio
async def test_flujo_completo_trabajo(authenticated_client: AsyncClient, db_session):
    """Probar flujo completo: Cliente → Trabajo → Pago"""
    
    # 1. Crear cliente
    cliente_data = {
        "tipo_cliente": "natural",
        "nombre_razon_social": "Cliente Test",
        "telefono": "0412-0000000",
        "cedula": "V-99999999",
        "direccion": "Test Address"
    }
    
    response = await authenticated_client.post(
        "/clientes/nuevo",
        data=cliente_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Obtener el cliente creado
    clientes = await db_session.execute(select(Cliente).where(Cliente.cedula == "V-99999999"))
    cliente = clientes.scalars().first()
    assert cliente is not None
    
    # 2. Crear trabajo
    trabajo_data = {
        "cliente_id": cliente.id,
        "nombre_trabajo": "Trabajo Integración",
        "monto_total": "2000.00",
        "estado": "pendiente",
        "fecha_inicio": "2024-01-01",
        "metodo_pago": "efectivo_usd",
        "tipo_trabajo": "rotulado_instalacion"
    }
    
    response = await authenticated_client.post(
        "/trabajos",
        data=trabajo_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Obtener el trabajo creado
    trabajos = await db_session.execute(select(Trabajo).where(Trabajo.cliente_id == cliente.id))
    trabajo = trabajos.scalars().first()
    assert trabajo is not None
    
    # 3. Registrar pago
    pago_data = {
        "monto_usd": "1000.00",
        "tasa_actual": "36.50",
        "metodo_pago": "efectivo_usd",
        "fecha_pago": "2024-01-15T12:00"
    }
    
    response = await authenticated_client.post(
        f"/trabajos/{trabajo.id}/registrar-pago",
        data=pago_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    await db_session.refresh(trabajo)
    assert trabajo.porcentaje_pagado == 50