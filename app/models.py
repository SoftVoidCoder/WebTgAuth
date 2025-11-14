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



class LikedTrack(Base):
    __tablename__ = "liked_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    track_id = Column(String(255), nullable=False)  # Формат: trackId_albumId
    track_title = Column(String(500), nullable=False)
    track_artists = Column(String(1000), nullable=False)  # JSON строка с артистами
    track_cover_uri = Column(Text, nullable=True)
    track_album = Column(String(500), nullable=True)
    liked_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

