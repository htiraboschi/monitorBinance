from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

async def get_db_session(db_file_path: str):
    SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{db_file_path}?check_same_thread=False"

    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    return SessionLocal()
    