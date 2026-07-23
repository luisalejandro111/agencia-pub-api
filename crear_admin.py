import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Usuario
from app.auth import hash_password

DATABASE_URL =  "postgresql+asyncpg://neondb_owner:npg_F7CI2PbSfake@ep-fragrant-night-atdv1uju.c-9.us-east-1.aws.neon.tech/neondb"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        user = Usuario(
            email='admin@admin.com',
            username='admin',
            nombre='Administrador',
            hashed_password=hash_password('admin123'),
            rol='administrador',
            activo=True
        )
        session.add(user)
        await session.commit()
        print('✅ Usuario admin creado: admin@admin.com / admin123')

asyncio.run(main())
