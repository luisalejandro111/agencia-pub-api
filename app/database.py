# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# 🔥 CONFIGURACIÓN CON RECONEXIÓN AUTOMÁTICA
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_size=5,                # Conexiones en el pool
    max_overflow=10,            # Conexiones extra cuando el pool está lleno
    pool_pre_ping=True,         # 👈 VERIFICA LA CONEXIÓN ANTES DE USARLA
    pool_recycle=3600,          # Reciclar conexiones cada hora
    pool_timeout=30             # Timeout para obtener conexión
)

# Sesión asíncrona
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base para los modelos
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


