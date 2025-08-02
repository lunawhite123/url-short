from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import URL, URLBase, DBURL
from database import get_db, Base, engine
from datetime import datetime
import secrets

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        conn.run_sync(Base.metadata.create_all)

@app.post('/short', response_model=URL, status_code=status.HTTP_201_CREATED)
async def short(url: URLBase, db: AsyncSession = Depends(get_db)):
    short_code = secrets.token_urlsafe(6)
    db_url = DBURL(
        long_url=str(url.long_url),
        short_code=short_code,
        created_at=datetime.now()
    )
    db.add(db_url)
    await db.commit()
    await db.refresh(db_url)

    return db_url

@app.get('/{short_code}', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def long(short_code: str, db: AsyncSession = Depends(get_db)):
    stmt = select(DBURL).filter_by(short_code=short_code, is_active=True)

    result = await db.execute(stmt)

    db_url = result.scalar_one_or_none()

    if db_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='short code not found or inactive')
    
    return RedirectResponse(url=db_url.long_url)

@app.get('/')
async def start():
    return 'Lunas api'

