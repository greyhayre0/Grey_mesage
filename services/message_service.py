from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models.user import Users
from models.chat import ChatParticipants
from models.message import Messages
from schemas.message import MessageCreate
from websocket.connection_manager import manager
from core.config import settings

class MessageService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_chat_messages(self, chat_id: int, user_id: int, limit: int = 50):
        participant = self.db.query(ChatParticipants).filter(
            ChatParticipants.chat_id == chat_id,
            ChatParticipants.user_id == user_id
        ).first()
        
        if not participant:
            return []
        
        week_ago = datetime.utcnow() - timedelta(days=settings.MESSAGES_RETENTION_DAYS)
        
        messages = self.db.query(Messages).filter(
            Messages.chat_id == chat_id,
            Messages.timestamp >= week_ago
        ).order_by(Messages.timestamp.desc()).limit(limit).all()
        
        for msg in messages:
            if msg.sender_id != user_id and not msg.is_read:
                msg.is_read = True
        self.db.commit()
        
        return [
            {
                "id": msg.id,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sender_id": msg.sender_id,
                "sender_name": msg.sender.nickname,
                "sender_avatar": msg.sender.profileimage,
                "is_mine": msg.sender_id == user_id,
                "is_read": msg.is_read
            }
            for msg in messages
        ]
    
    def send_message(self, message: MessageCreate, user: Users):
        participant = self.db.query(ChatParticipants).filter(
            ChatParticipants.chat_id == message.chat_id,
            ChatParticipants.user_id == user.id
        ).first()
        
        if not participant:
            return None
        
        new_message = Messages(
            content=message.content,
            sender_id=user.id,
            chat_id=message.chat_id,
            timestamp=datetime.utcnow(),
            is_read=False
        )
        
        self.db.add(new_message)
        self.db.commit()
        self.db.refresh(new_message)
        
        # Отправка через WebSocket
        message_data = {
            "type": "new_message",
            "message": {
                "id": new_message.id,
                "content": new_message.content,
                "sender_id": new_message.sender_id,
                "sender_name": user.nickname,
                "timestamp": new_message.timestamp.isoformat(),
                "chat_id": new_message.chat_id
            }
        }
        
        return {
            "id": new_message.id,
            "content": new_message.content,
            "timestamp": new_message.timestamp.isoformat(),
            "sender_id": new_message.sender_id,
            "sender_name": user.nickname
        }