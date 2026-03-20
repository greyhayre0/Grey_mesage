from fastapi import Depends, Cookie
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.security import get_session
from models.user import Users

def get_current_user(
    session_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[Users]:
    """Получение текущего пользователя"""
    session_data = get_session(session_token)
    if not session_data:
        return None
    
    return db.query(Users).filter(Users.id == session_data['user_id']).first()