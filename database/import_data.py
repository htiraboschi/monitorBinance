import asyncio
from models import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./monitorBinance.db"

async def create_tables():
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True  # Opcional: muestra las consultas SQL generadas
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # ¡Ejecuta el DDL de forma asíncrona!
    
    print("Tablas creadas exitosamente")

if __name__ == "__main__":
    asyncio.run(create_tables())  # Ejecuta la corrutina asíncrona