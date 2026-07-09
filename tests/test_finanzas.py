# tests/test_finanzas.py
import pytest
from httpx import AsyncClient
from datetime import date, datetime
from main import app
from app.models import GastoDiario, CierreCaja

@pytest.mark.asyncio
async def test_crear_gasto(authenticated_client: AsyncClient, db_session):
    """Probar creación de gasto"""
    form_data = {
        "monto": "100.00",
        "descripcion": "Compra de materiales",
        "categoria_id": "1",
        "subcategoria_id": "1",
        "fecha": date.today().isoformat()
    }
    
    response = await authenticated_client.post(
        "/finanzas/gastos/crear",
        data=form_data,
        follow_redirects=True
    )
    
    assert response.status_code == 200
    
    # Verificar que se creó
    gastos = await db_session.execute(select(GastoDiario))
    gasto = gastos.scalars().first()
    assert gasto is not None
    assert float(gasto.monto) == 100.0

@pytest.mark.asyncio
async def test_listar_gastos(authenticated_client: AsyncClient, db_session):
    """Probar listado de gastos"""
    gasto = GastoDiario(
        monto=50.0,
        descripcion="Gasto de prueba",
        categoria_id=1,
        subcategoria_id=1,
        fecha=date.today()
    )
    db_session.add(gasto)
    await db_session.commit()
    
    response = await authenticated_client.get("/finanzas/gastos")
    assert response.status_code == 200
    assert "Gasto de prueba" in response.text

@pytest.mark.asyncio
async def test_cierre_caja(authenticated_client: AsyncClient, db_session):
    """Probar cierre de caja"""
    # Primero crear algunos gastos
    gasto = GastoDiario(
        monto=50.0,
        descripcion="Gasto de prueba",
        categoria_id=1,
        subcategoria_id=1,
        fecha=date.today()
    )
    db_session.add(gasto)
    await db_session.commit()
    
    response = await authenticated_client.get("/finanzas/caja-diaria/nuevo")
    assert response.status_code == 200
    assert "Cierre" in response.text