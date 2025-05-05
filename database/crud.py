from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Regla

#async def create_entidad(db: AsyncSession, entidad_data: dict):
async def create_regla(db: AsyncSession, regla: Regla):
    db.add(regla)
    await db.commit()
    await db.refresh(regla)  # Para obtener el ID generado
    return regla

async def get_reglas(db: AsyncSession):
    result = await db.execute(select(Regla))
    reglas = result.scalars().all()
    return reglas


async def get_regla_by_id(db: AsyncSession, regla_id: int):
    result = await db.execute(select(Regla).where(Regla.regla_id == regla_id))
    regla = result.scalar_one_or_none()
    return regla

#borro una regla
async def delete_regla(db: AsyncSession, regla: Regla) -> None:
    await db.delete(regla)
    await db.commit()
        