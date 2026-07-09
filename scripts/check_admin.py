# scripts/check_admin.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_maker
from app.models import Usuario
from sqlalchemy import select

async def check_admin():
    print("\n🔍 Verificando administrador...\n")
    
    async with async_session_maker() as db:
        result = await db.execute(select(Usuario).where(Usuario.rol == "administrador"))
        admin = result.scalar_one_or_none()
        
        if admin:
            print(f"✅ Administrador encontrado:")
            print(f"   ID: {admin.id}")
            print(f"   Nombre: {admin.nombre}")
            print(f"   Email: {admin.email}")
            print(f"   Username: {admin.username}")
            print(f"   Activo: {'✅' if admin.activo else '❌'}")
        else:
            print("❌ No hay administrador en el sistema")
            print("Ejecuta: python scripts/crear_admin.py")
    
    print()

if __name__ == "__main__":
    asyncio.run(check_admin())