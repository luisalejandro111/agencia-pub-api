"""
Script para crear las tablas de recetas
"""
import asyncio
from sqlalchemy import text
from app.database import engine
from app.models import Base

async def main():
    async with engine.begin() as conn:
        # Crear solo las nuevas tablas (no afecta las existentes)
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tablas de recetas creadas exitosamente")
        print("   - receta_producto")
        print("   - receta_material")
        print("\n🎉 Ahora puedes acceder a /recetas para crear tus productos")

if __name__ == "__main__":
    asyncio.run(main())
