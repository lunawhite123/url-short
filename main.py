from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import DBURL, User
from database import get_db, Base, engine
from datetime import datetime, timezone
from schemas import URL, URLBase, UserCreate, UserResponse
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
app = FastAPI()

def hash_password(password: str) -> str:
    hashed = pwd_context.hash(password)
    return hashed

def check_password(plain_password: str, hashed_password: str) -> bool:
    checked = pwd_context.check(plain_password, hashed_password)
    return checked

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post('/short', response_model=URL, status_code=status.HTTP_201_CREATED)
async def short(url: URLBase, db: AsyncSession = Depends(get_db)):
    short_code = secrets.token_urlsafe(6)
    db_url = DBURL(
        long_url=str(url.long_url),
        short_code=short_code,
        created_at=datetime.now(timezone.utc)
    )

    db.add(db_url)
    await db.commit()
    await db.refresh(db_url)
    return db_url

@app.get('/{short_code}', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def long(short_code: str, db: AsyncSession = Depends(get_db)):
    
    code = select(DBURL).filter_by(short_code=short_code, is_active=True)
    result = await db.execute(code)
    result = result.scalar_one_or_none()

    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='short code not found or inactive')
    
    return RedirectResponse(url=result.long_url)

@app.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    
    user_data.password = hash_password(user_data.password)
    are_same = select(User).filter_by(username=user_data.username, is_active=True)
    
    result = await db.execute(are_same)
    result = result.scalar_one_or_none()
    if result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Имя пользователя уже найдено в системе, пожалуйста выберите другое имя')
    
    user = User(
        username=user_data.username,
        hashed_password=user_data.password
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user
    
@app.get('/')
async def start():
    return 'Lunas api'

