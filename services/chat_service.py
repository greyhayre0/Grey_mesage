from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from models.user import Users
from models.chat import Chats, ChatParticipants
from models.message import Messages
from schemas.chat import ChatCreate
from websocket.connection_manager import manager

class ChatService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_chats(self, user_id: int):
        chats = self.db.query(Chats).join(
            ChatParticipants
        ).filter(
            ChatParticipants.user_id == user_id
        ).all()
        
        result = []
        for chat in chats:
            last_message = self.db.query(Messages).filter(
                Messages.chat_id == chat.id
            ).order_by(Messages.timestamp.desc()).first()
            
            unread_count = self.db.query(Messages).filter(
                Messages.chat_id == chat.id,
                Messages.is_read == False,
                Messages.sender_id != user_id
            ).count()
            
            chat_name = chat.name
            other_participant = None
            
            if not chat.is_group and not chat_name:
                other_participant = self.db.query(Users).join(
                    ChatParticipants
                ).filter(
                    ChatParticipants.chat_id == chat.id,
                    Users.id != user_id
                ).first()
                if other_participant:
                    chat_name = other_participant.nickname
            
            if chat.is_group:
                profileimage = '/static/default-avatar.png'
            else:
                profileimage = other_participant.profileimage if other_participant else '/static/default-avatar.png'
            
            result.append({
                "id": chat.id,
                "name": chat_name or f"Чат {chat.id}",
                "profileimage": profileimage,
                "is_group": chat.is_group,
                "last_message": last_message.content if last_message else None,
                "last_message_time": last_message.timestamp.isoformat() if last_message else None,
                "unread_count": unread_count,
                "created_at": chat.created_at.isoformat()
            })
        
        return result
    
    def create_chat(self, chat_data: ChatCreate, user_id: int):
        all_participants = list(set(chat_data.participant_ids + [user_id]))
        is_group = len(all_participants) > 2
        
        new_chat = Chats(
            name=chat_data.name,
            is_group=is_group,
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_chat)
        self.db.commit()
        self.db.refresh(new_chat)
        
        for participant_id in all_participants:
            participant = ChatParticipants(
                user_id=participant_id,
                chat_id=new_chat.id,
                joined_at=datetime.utcnow()
            )
            self.db.add(participant)
        
        self.db.commit()
        
        return {"id": new_chat.id, "name": new_chat.name}
    
    def delete_chat(self, chat_id: int, user_id: int):
        participant = self.db.query(ChatParticipants).filter(
            ChatParticipants.chat_id == chat_id,
            ChatParticipants.user_id == user_id
        ).first()
        
        if not participant:
            return {"success": False, "error": "Чат не найден или нет доступа"}
        
        self.db.query(Messages).filter(Messages.chat_id == chat_id).delete()
        self.db.query(ChatParticipants).filter(ChatParticipants.chat_id == chat_id).delete()
        
        chat = self.db.query(Chats).filter(Chats.id == chat_id).first()
        if chat:
            self.db.delete(chat)
        
        self.db.commit()
        
        manager.disconnect_chat(chat_id)
        
        return {"success": True}