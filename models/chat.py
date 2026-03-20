from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from core.database import Base

class Chats(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    messages = relationship("Messages", back_populates="chat")
    participants = relationship("ChatParticipants", back_populates="chat")

class ChatParticipants(Base):
    __tablename__ = "chat_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    user = relationship("Users", back_populates="chat_participations")
    chat = relationship("Chats", back_populates="participants")