from pydantic import BaseModel, HttpUrl
from datetime import datetime

class URLBase(BaseModel):
    long_url: HttpUrl

class URL(URLBase):
    id: int
    short_code: str
    active: bool = True
    created_at: datetime
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool = True
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class TokenData(BaseModel):
    username: str | None