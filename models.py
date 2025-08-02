from sqlalchemy import Column, String, Integer, Boolean, DateTime
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from database import Base

class URLBase(BaseModel):
    long_url: HttpUrl

class URL(URLBase):
    id: int
    short_code: str
    active: bool = True
    created_at: datetime

class Config:
    from_attributes = True

class DBURL(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    long_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now())
