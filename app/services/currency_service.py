from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from decimal import Decimal
from app.models import TasaCambio

class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_tasa(self, sede_id: int = None) -> Decimal:
        """Obtiene el valor actual de la tasa (filtrada por sede si se indica)"""
        # 🔥 SI PIDEN TASA DE UNA SEDE ESPECÍFICA
        if sede_id:
            resultado = await self.db.execute(
                select(TasaCambio)
                .where(TasaCambio.sede_id == sede_id)
                .order_by(TasaCambio.id.desc())
                .limit(1)
            )
            tasa = resultado.scalar_one_or_none()
            if tasa:
                return tasa.valor
            # 🔥 FALLBACK: si la sede aún no tiene tasa propia,
            # usa la última tasa registrada (no rompe sedes nuevas ni otros módulos)
        
        resultado = await self.db.execute(
            select(TasaCambio).order_by(TasaCambio.id.desc()).limit(1)
        )
        tasa = resultado.scalar_one_or_none()
        
        if not tasa:
            return Decimal("1.0")
        
        return tasa.valor
    
    async def get_all_tasas(self, limit: int = 50, sede_id: int = None):
        """Obtiene el historial de tasas (filtrado por sede si se indica)"""
        query = select(TasaCambio)
        if sede_id:
            query = query.where(TasaCambio.sede_id == sede_id)  # 🔥 FILTRO POR SEDE
        query = query.order_by(TasaCambio.id.desc()).limit(limit)
        
        resultado = await self.db.execute(query)
        return resultado.scalars().all()
    
    async def set_tasa(self, valor: Decimal, usuario_id: int, sede_id: int = None) -> TasaCambio:
        """Guarda un nuevo valor de tasa con hora de Venezuela y sede"""
        # 🔥 OBTENER LA HORA ACTUAL DE VENEZUELA (UTC-4)
        ahora_utc = datetime.utcnow()
        ahora_venezuela = ahora_utc - timedelta(hours=4)
        
        nueva_tasa = TasaCambio(
            valor=valor,
            fecha_actualizacion=ahora_venezuela,  # ← Guardamos hora de Venezuela
            actualizado_por=usuario_id,
            sede_id=sede_id  # 🔥 ASIGNAR SEDE ACTIVA
        )
        
        self.db.add(nueva_tasa)
        await self.db.commit()
        await self.db.refresh(nueva_tasa)
        
        print(f"✅ Tasa guardada: {valor} | Sede: {sede_id}")
        print(f"   Hora UTC: {ahora_utc.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"   Hora Venezuela: {ahora_venezuela.strftime('%d/%m/%Y %H:%M:%S')}")
        
        return nueva_tasa