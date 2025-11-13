from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    photo_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class Gift(Base):
    __tablename__ = "gifts"
    
    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(100))
    image_url = Column(String(500))
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    seller = relationship("User", backref="gifts")

# Добавляем связь в модель User
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    photo_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)