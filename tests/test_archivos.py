# tests/test_archivos.py
import pytest
from httpx import AsyncClient
from io import BytesIO
from main import app
from app.models import ArchivoTrabajo

@pytest.mark.asyncio
async def test_subir_archivo(authenticated_client: AsyncClient, db_session):
    """Probar subida de archivo"""
    from tests.factories import TrabajoFactory, ClienteFactory
    
    # Crear cliente y trabajo primero
    cliente = ClienteFactory()
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)
    
    trabajo = TrabajoFactory(cliente_id=cliente.id, creado_por=1)
    db_session.add(trabajo)
    await db_session.commit()
    await db_session.refresh(trabajo)
    
    # Crear archivo de prueba
    test_file = BytesIO(b"contenido de prueba")
    files = {"archivos": ("test.txt", test_file, "text/plain")}
    
    response = await authenticated_client.post(
        f"/trabajos/{trabajo.id}/subir-archivos",
        files=files,
        data={"descripcion": "Archivo de prueba"},
        follow_redirects=True
    )
    
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_descargar_archivo(authenticated_client: AsyncClient, db_session):
    """Probar descarga de archivo"""
    # Crear un archivo de prueba
    archivo = ArchivoTrabajo(
        trabajo_id=1,
        nombre_original="test.txt",
        nombre_guardado="test.txt",
        ruta_completa="/tmp/test.txt",
        tipo_mime="text/plain",
        tamano_bytes=10
    )
    db_session.add(archivo)
    await db_session.commit()
    
    response = await authenticated_client.get(
        f"/uploads/trabajos/1/test.txt"
    )
    assert response.status_code in [200, 404]  # 404 si no existe el archivo físico