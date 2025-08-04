from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import DBURL, User
from schemas import URL, URLBase, UserCreate, UserResponse, Token, TokenData

from database import get_db, Base, engine
from datetime import datetime, timezone, timedelta

from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets

pwd_context = CryptContext(schemes=['sha256_crypt'], deprecated='auto')

SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

app = FastAPI()

def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    
    if not expires_delta:
        time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else: 
        time = datetime.now(timezone.utc) + expires_delta
    
    data['exp'] = time
    token = jwt.encode(claims=data, key=SECRET_KEY, algorithm=ALGORITHM)
    return token

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        
        tokendata = TokenData(username=username)
        
    except JWTError:
        raise credentials_exception
    
    user = await db.execute(select(User).filter_by(username=username, is_active=True))
    user = user.scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user
    
def hash_password(password: str) -> str:
    hashed_password = pwd_context.hash(password)
    return hashed_password

def check_password(plain_password: str, hashed_password: str) -> bool:
    checked = pwd_context.verify(plain_password, hashed_password)
    return checked

@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post('/short', response_model=URL, status_code=status.HTTP_201_CREATED)
async def short(url: URLBase, db: AsyncSession = Depends(get_db)) -> DBURL:
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

@app.post('/token', response_model=Token)
async def get_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> Token:
    
    user_result = await db.execute(select(User).filter_by(username=form_data.username, is_active=True))
    user = user_result.scalar_one_or_none()
    
    if not user or not check_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Неверное имя пользователя или пароль')
    
    new_token = create_token(data={'sub': user.username})
    token = Token(access_token=new_token)
    return token

@app.get('/users/me', response_model=UserResponse)
async def get_user(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> User:
    return current_user
    

    
@app.get('/')
async def start():
    return 'Lunas api'