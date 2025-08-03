from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = 'postgresql+asyncpg://user:password@localhost:5432/shortener_auth_db'
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()

AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as sesh:
        yield sesh


















