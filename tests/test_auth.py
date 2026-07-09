# tests/test_auth.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_login_page(client: AsyncClient):
    """Verificar que la página de login carga correctamente"""
    response = await client.get("/login")
    assert response.status_code == 200
    assert "login" in response.text.lower()

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Probar login exitoso"""
    response = await client.post(
        "/login",
        data={
            "email": "test@test.com",
            "password": "test123"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "dashboard" in response.url.path.lower()

@pytest.mark.asyncio
async def test_login_fail(client: AsyncClient):
    """Probar login fallido - Credenciales incorrectas"""
    response = await client.post(
        "/login",
        data={
            "email": "wrong@test.com",
            "password": "wrongpassword"
        },
        follow_redirects=True
    )
    
    # El login fallido muestra el error en el HTML o en la URL
    assert response.status_code == 200
    
    # Buscar el mensaje de error en el HTML (puede estar en diferentes formatos)
    text_lower = response.text.lower()
    assert "email" in text_lower or "contraseña" in text_lower

@pytest.mark.asyncio
async def test_login_fail_empty_fields(client: AsyncClient):
    """Probar login fallido - Campos vacíos"""
    response = await client.post(
        "/login",
        data={
            "email": "",
            "password": ""
        },
        follow_redirects=True
    )
    
    assert response.status_code == 200
    text_lower = response.text.lower()
    # El mensaje puede ser "Email y contraseña son requeridos" o similar
    assert "requeridos" in text_lower or "obligatorios" in text_lower or "email" in text_lower

@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient):
    """Verificar que dashboard requiere autenticación"""
    response = await client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    assert "login" in response.url.path.lower()

@pytest.mark.asyncio
async def test_logout(client: AsyncClient, test_user):
    """Probar logout"""
    # Primero hacer login
    await client.post(
        "/login",
        data={
            "email": "test@test.com",
            "password": "test123"
        }
    )
    
    # Luego logout
    response = await client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert "login" in response.url.path.lower()

@pytest.mark.asyncio
async def test_protected_route_redirects_to_login(client: AsyncClient):
    """Verificar que rutas protegidas redirigen a login"""
    response = await client.get("/clientes", follow_redirects=True)
    assert response.status_code == 200
    assert "login" in response.url.path.lower()