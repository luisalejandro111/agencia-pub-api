import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import Cliente

@pytest.mark.asyncio
async def test_listar_clientes(authenticated_client: AsyncClient, db_session):
    """Probar listado de clientes"""
    from tests.factories import ClienteFactory
    
    # Crear algunos clientes de prueba
    for i in range(3):
        cliente = ClienteFactory()
        db_session.add(cliente)
    await db_session.commit()
    
    response = await authenticated_client.get("/clientes")
    assert response.status_code == 200
    assert "Clientes" in response.text

@pytest.mark.asyncio
async def test_crear_cliente(authenticated_client: AsyncClient):
    """Probar creación de cliente"""
    form_data = {
        "tipo_cliente": "natural",
        "nombre_razon_social": "Juan Perez Test",
        "telefono": "0412-1234567",
        "email": "juan@test.com",
        "cedula": "V-12345678",
        "direccion": "Calle 123",
        "activo": "true"
    }
    
    response = await authenticated_client.post(
        "/clientes/nuevo",
        data=form_data,
        follow_redirects=True
    )
    
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_crear_cliente_duplicado(authenticated_client: AsyncClient, db_session):
    """Probar que no se permiten clientes duplicados"""
    from tests.factories import ClienteFactory
    
    # Crear cliente existente
    cliente = ClienteFactory(cedula="V-12345678")
    db_session.add(cliente)
    await db_session.commit()
    
    # Intentar crear duplicado
    form_data = {
        "tipo_cliente": "natural",
        "nombre_razon_social": "Otro Nombre",
        "telefono": "0412-1234567",
        "cedula": "V-12345678",  # Misma cédula
        "direccion": "Calle 123"
    }
    
    response = await authenticated_client.post(
        "/clientes/nuevo",
        data=form_data,
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert "Ya existe" in response.text

@pytest.mark.asyncio
async def test_editar_cliente(authenticated_client: AsyncClient, db_session):
    """Probar edición de cliente"""
    from tests.factories import ClienteFactory
    
    cliente = ClienteFactory()
    db_session.add(cliente)
    await db_session.commit()
    
    form_data = {
        "tipo_cliente": "natural",
        "nombre_razon_social": "Nombre Actualizado",
        "telefono": "0412-9999999",
        "email": "actualizado@test.com",
        "activo": "true"
    }
    
    response = await authenticated_client.post(
        f"/clientes/{cliente.id}/editar",
        data=form_data,
        follow_redirects=True
    )
    
    assert response.status_code == 200
    await db_session.refresh(cliente)
    assert cliente.nombre_razon_social == "Nombre Actualizado"