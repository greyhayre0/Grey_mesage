from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.dependencies import get_current_user
from services.chat_service import ChatService
from schemas.chat import ChatCreate
from models.user import Users

router = APIRouter()

@router.get("/chats")
async def get_user_chats(
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = ChatService(db)
    return service.get_user_chats(user.id)

@router.post("/chats")
async def create_chat(
    chat_data: ChatCreate,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = ChatService(db)
    return service.create_chat(chat_data, user.id)

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = ChatService(db)
    return service.delete_chat(chat_id, user.id)