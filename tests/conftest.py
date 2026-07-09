# tests/conftest.py
import sys
import os
import pytest
import asyncio

# ============================================
# AGREGAR LA RAIZ AL PATH
# ============================================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

print(f"📂 Root directory: {ROOT_DIR}")

# ============================================
# IMPORTAR DESDE LA RAIZ
# ============================================
from main import app
from app.database import Base, get_db
from app.models import Usuario, Cliente, Empleado, Trabajo
from app.auth import hash_password

# ============================================
# IMPORTAR FÁBRICAS
# ============================================
from tests.factories import ClienteFactory, EmpleadoFactory, TrabajoFactory

# ============================================
# CONFIGURACIÓN DE ASYNCIO
# ============================================
@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para todas las pruebas"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# ============================================
# BASE DE DATOS DE PRUEBA
# ============================================
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, text

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
SYNC_DATABASE_URL = "sqlite:///./test.db"

# Crear engine asíncrono para pruebas
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# ============================================
# FIXTURES
# ============================================
@pytest.fixture(scope="function")
async def db_session():
    """Fixture para la sesión de base de datos de prueba"""
    # Paso 1: Crear tablas usando SQLite síncrono
    sync_engine = create_engine(SYNC_DATABASE_URL)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()
    
    # Paso 2: Verificar que las tablas se crearon
    async with test_engine.begin() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = result.fetchall()
        print(f"📋 Tablas creadas: {[t[0] for t in tables]}")
    
    # Paso 3: Crear sesión y asignarla a las fábricas
    async with TestingSessionLocal() as session:
        # 👇 ASIGNAR LA SESIÓN A LAS FÁBRICAS
        ClienteFactory._meta.sqlalchemy_session = session
        EmpleadoFactory._meta.sqlalchemy_session = session
        TrabajoFactory._meta.sqlalchemy_session = session
        
        yield session
    
    # Paso 4: Limpiar después de cada test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session):
    """Fixture para el cliente HTTP"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def test_user(db_session):
    """Crear usuario de prueba - CORREGIDO con username"""
    user = Usuario(
        email="test@test.com",
        username="testuser",  # 👈 AGREGADO - no puede ser NULL
        nombre="Test User",
        hashed_password=hash_password("test123"),
        rol="admin",
        activo=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
async def authenticated_client(client, test_user):
    """Cliente autenticado para pruebas"""
    response = await client.post(
        "/login",
        data={
            "email": "test@test.com",
            "password": "test123"
        }
    )
    client.cookies = response.cookies
    return client