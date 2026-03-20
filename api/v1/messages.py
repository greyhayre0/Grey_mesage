from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from services.message_service import MessageService
from schemas.message import MessageCreate
from models.user import Users
from websocket.connection_manager import manager

router = APIRouter()

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int,
    limit: int = 50,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = MessageService(db)
    return service.get_chat_messages(chat_id, user.id, limit)

@router.post("/messages")
async def send_message(
    message: MessageCreate,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = MessageService(db)
    result = service.send_message(message, user)
    
    if not result:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    
    # Отправляем через WebSocket
    await manager.broadcast_to_chat(
        message.chat_id,
        {
            "type": "new_message",
            "message": result
        }
    )
    
    return result

@router.get("/messages/unread-counts")
async def get_unread_counts(
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить количество непрочитанных сообщений по каждому чату"""
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = MessageService(db)
    return service.get_unread_counts(user.id)

@router.post("/messages/mark-chat-read/{chat_id}")
async def mark_chat_as_read(
    chat_id: int,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отметить все сообщения в чате как прочитанные"""
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = MessageService(db)
    result = service.mark_chat_as_read(chat_id, user.id)
    
    if not result:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    
    return {"status": "success"}