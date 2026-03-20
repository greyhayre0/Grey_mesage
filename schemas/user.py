from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re
from enum import Enum

class UserRole(str, Enum): # Вообще дублирование но пока тестово так
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

class UserAuth(BaseModel):
    username: str = Field(..., min_length=4, max_length=50, description="Логин от 4 до 50 символов")
    password: str = Field(..., max_length=100, description="Пароль от 8 до 100 символов")

    @field_validator('username')
    @classmethod
    def validate(cls, v):
        """Валидация логина"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Логин должен содержать только английские буквы, цифры и знак подчеркивания')
        reserved = ['admin', 'root', 'system', 'moderator', 'support', 'administrator']
        if v.lower() in reserved:
            raise ValueError(f'Имя "{v}" зарезервировано и не может быть использовано')
        if v.lower().startswith('user_'):
            raise ValueError('Логин не может начинаться с "user_"')
        if v.lower().endswith('_bot'):
            raise ValueError('Логин не может заканчиваться на "_bot"')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Валидация пароля"""
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if not re.match(r'^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]+$', v):
            raise ValueError('Пароль может содержать только латинские буквы, цифры и специальные символы')
        common_passwords = [
                'password123', 'qwerty123', '12345678', 'admin123',
                'password1', '123456789', '11111111', 'abcdefgh'
            ]
        if v.lower() in common_passwords:
                raise ValueError('Слишком простой пароль')
        if re.search(r'(.)\1{3,}', v):
            raise ValueError('Пароль содержит слишком много повторяющихся символов')
        return v
    

class UserResponse(BaseModel):
    id: int
    username: str = Field(..., min_length=4, max_length=50)
    nickname: str = Field(..., min_length=1, max_length=50)
    profileimage: Optional[str]
    created_at: datetime
    role: UserRole
    last_seen: Optional[datetime]

    @field_validator('nickname')
    @classmethod
    def validate_nickname(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Никнейм не может быть пустым')
        if len(v) > 50:
            raise ValueError('Никнейм не может быть длиннее 50 символов')
        return v.strip()
    class Config:
        from_attributes = True  # Для работы с SQLAlchemy моделями

class UserSearchResponse(BaseModel):
    id: int
    username: str = Field(..., min_length=5, max_length=50)
    nickname: str = Field(..., min_length=1, max_length=50)
    role: UserRole
    class Config:
        from_attributes = True

class UserRoleUpdate(BaseModel):
    """Схема для обновления роли пользователя (только для админов)"""
    role: UserRole
    
    class Config:
        from_attributes = True