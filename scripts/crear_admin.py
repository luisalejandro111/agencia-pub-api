# scripts/crear_admin.py
import asyncio
import sys
import os
import getpass

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_maker
from app.models import Usuario
from app.auth import hash_password
from app.config import settings
from sqlalchemy import select

async def crear_admin():
    print("\n" + "="*50)
    print("🔐 CREACIÓN DE ADMINISTRADOR")
    print("="*50 + "\n")
    
    async with async_session_maker() as db:
        # Verificar si ya existe un admin
        result = await db.execute(select(Usuario).where(Usuario.rol == "administrador"))
        admin_existente = result.scalar_one_or_none()
        
        if admin_existente:
            print(f"✅ Ya existe un administrador:")
            print(f"   Nombre: {admin_existente.nombre}")
            print(f"   Email: {admin_existente.email}")
            print(f"   Username: {admin_existente.username}")
            print("\n⚠️ No es necesario crear otro administrador.")
            print(f"🔗 Inicia sesión en: {settings.BASE_URL}/login\n")
            return
        
        print("📝 Ingresa los datos del administrador:\n")
        
        # Solicitar datos
        nombre = input("Nombre completo: ").strip()
        while not nombre:
            print("❌ El nombre es requerido")
            nombre = input("Nombre completo: ").strip()
        
        username = input("Username: ").strip().lower()
        while not username:
            print("❌ El username es requerido")
            username = input("Username: ").strip().lower()
        
        email = input("Email: ").strip().lower()
        while not email:
            print("❌ El email es requerido")
            email = input("Email: ").strip().lower()
        
        password = getpass.getpass("Contraseña (mínimo 6 caracteres): ")
        while len(password) < 6:
            print("❌ La contraseña debe tener al menos 6 caracteres")
            password = getpass.getpass("Contraseña (mínimo 6 caracteres): ")
        
        password_confirm = getpass.getpass("Confirmar contraseña: ")
        while password != password_confirm:
            print("❌ Las contraseñas no coinciden")
            password = getpass.getpass("Contraseña (mínimo 6 caracteres): ")
            password_confirm = getpass.getpass("Confirmar contraseña: ")
        
        # Verificar username único
        result = await db.execute(select(Usuario).where(Usuario.username == username))
        if result.scalar_one_or_none():
            print(f"❌ El username '{username}' ya existe")
            return
        
        # Verificar email único
        result = await db.execute(select(Usuario).where(Usuario.email == email))
        if result.scalar_one_or_none():
            print(f"❌ El email '{email}' ya existe")
            return
        
        # Crear admin
        try:
            admin = Usuario(
                nombre=nombre,
                username=username,
                email=email,
                hashed_password=hash_password(password),
                rol="administrador",
                activo=True
            )
            
            db.add(admin)
            await db.commit()
            
            print("\n" + "="*50)
            print("✅ ADMINISTRADOR CREADO EXITOSAMENTE")
            print("="*50)
            print(f"\n📋 Datos del administrador:")
            print(f"   Nombre: {nombre}")
            print(f"   Email: {email}")
            print(f"   Username: {username}")
            print(f"   Rol: administrador")
            print(f"\n🔗 Inicia sesión en: {settings.BASE_URL}/login")
            print("\n⚠️  RECOMENDACIÓN: Cambia la contraseña después del primer login.")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error al crear administrador: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(crear_admin())