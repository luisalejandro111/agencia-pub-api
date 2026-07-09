# app/services/currency_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from decimal import Decimal
from app.models import TasaCambio

class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_tasa(self) -> Decimal:
        """Obtiene el valor actual de la tasa"""
        resultado = await self.db.execute(
            select(TasaCambio).order_by(TasaCambio.id.desc()).limit(1)
        )
        tasa = resultado.scalar_one_or_none()
        
        if not tasa:
            return Decimal("1.0")
        
        return tasa.valor
    
    async def get_all_tasas(self, limit: int = 50):
        """Obtiene el historial de todas las tasas"""
        resultado = await self.db.execute(
            select(TasaCambio)
            .order_by(TasaCambio.id.desc())
            .limit(limit)
        )
        return resultado.scalars().all()
    
    async def set_tasa(self, valor: Decimal, usuario_id: int) -> TasaCambio:
        """Guarda un nuevo valor de tasa con hora de Venezuela"""
        # 🔥 OBTENER LA HORA ACTUAL DE VENEZUELA (UTC-4)
        # UTC es la hora universal, Venezuela es UTC-4
        ahora_utc = datetime.utcnow()
        ahora_venezuela = ahora_utc - timedelta(hours=4)
        
        nueva_tasa = TasaCambio(
            valor=valor,
            fecha_actualizacion=ahora_venezuela,  # ← Guardamos hora de Venezuela
            actualizado_por=usuario_id
        )
        
        self.db.add(nueva_tasa)
        await self.db.commit()
        await self.db.refresh(nueva_tasa)
        
        print(f"✅ Tasa guardada: {valor}")
        print(f"   Hora UTC: {ahora_utc.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   Hora Venezuela: {ahora_venezuela.strftime('%d/%m/%Y %H:%M:%S')}")
        
        return nueva_tasa