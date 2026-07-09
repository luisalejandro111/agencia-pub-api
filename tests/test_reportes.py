# tests/test_reportes.py
import pytest
from httpx import AsyncClient
from datetime import date, timedelta
from main import app

@pytest.mark.asyncio
async def test_reporte_diario(authenticated_client: AsyncClient):
    """Probar reporte diario"""
    hoy = date.today().isoformat()
    
    response = await authenticated_client.get(
        f"/caja/diario?fecha={hoy}"
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_reporte_semanal(authenticated_client: AsyncClient):
    """Probar reporte semanal"""
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    response = await authenticated_client.get(
        f"/reportes/semanal?fecha_inicio={inicio_semana}&fecha_fin={fin_semana}"
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_exportar_pdf(authenticated_client: AsyncClient):
    """Probar exportación de PDF"""
    hoy = date.today().isoformat()
    
    response = await authenticated_client.get(
        f"/caja/diario/exportar/pdf?fecha={hoy}"
    )
    assert response.status_code in [200, 303]

@pytest.mark.asyncio
async def test_exportar_excel(authenticated_client: AsyncClient):
    """Probar exportación de Excel"""
    hoy = date.today().isoformat()
    
    response = await authenticated_client.get(
        f"/caja/diario/exportar/excel?fecha={hoy}"
    )
    assert response.status_code in [200, 303]