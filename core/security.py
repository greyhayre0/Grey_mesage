import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from core.config import settings

# Хранилище сессий (в реальном проекте используйте Redis)
sessions: Dict[str, Dict[str, Any]] = {}

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Проверка пароля"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_session(user_id: int, username: str) -> str:
    """Создание сессии"""
    session_token = secrets.token_hex(32)
    sessions[session_token] = {
        'user_id': user_id,
        'username': username,
        'created_at': datetime.utcnow()
    }
    return session_token

def get_session(session_token: Optional[str]):
    """Получение сессии"""
    if not session_token or session_token not in sessions:
        return None
    
    session_data = sessions[session_token]
    
    # Проверка срока действия
    if datetime.utcnow() - session_data['created_at'] > timedelta(hours=settings.SESSION_EXPIRE_HOURS):
        del sessions[session_token]
        return None
    
    return session_data

def delete_session(session_token: str):
    """Удаление сессии"""
    if session_token in sessions:
        del sessions[session_token]