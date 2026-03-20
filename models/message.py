from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from core.database import Base

class Messages(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    sender_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # Отношения
    sender = relationship("Users", back_populates="sent_messages")
    chat = relationship("Chats", back_populates="messages")