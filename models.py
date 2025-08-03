from sqlalchemy import Column, String, Integer, Boolean, DateTime
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)    
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

class DBURL(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    long_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))