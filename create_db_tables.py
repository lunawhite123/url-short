import asyncio
from database import Base, engine
from models import DBURL

async def create_tables():
    print('Начинаю создание таблицы')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print('Таблица создана')

if __name__=='__main__':
    asyncio.run(create_tables())