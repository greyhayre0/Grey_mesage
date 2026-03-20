from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from core.database import Base
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    profileimage = Column(String, default="/static/default-avatar.png")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=True)
    role = Column(
        SQLAlchemyEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.USER,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint('LENGTH(username) >= 4', name='username_min_length'),
        CheckConstraint('LENGTH(username) <= 50', name='username_max_length'),
        CheckConstraint('LENGTH(nickname) >= 1', name='nickname_min_length'),
        CheckConstraint('LENGTH(nickname) <= 50', name='nickname_max_length'),
        CheckConstraint("role IN ('user', 'moderator', 'admin')",name='role_valid_values'),
    )

    
    # Отношения
    sent_messages = relationship("Messages", back_populates="sender")
    chat_participations = relationship("ChatParticipants", back_populates="user")

    def is_admin(self) -> bool:
        """Проверка, является ли пользователь администратором"""
        return self.role == UserRole.ADMIN
    
    def is_moderator(self) -> bool:
        """Проверка, является ли пользователь модератором"""
        return self.role == UserRole.MODERATOR
    
    def is_user(self) -> bool:
        """Проверка, является ли пользователь обычным пользователем"""
        return self.role == UserRole.USER
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Проверка, имеет ли пользователь необходимый уровень доступа"""
        role_level = {
            UserRole.USER: 1,
            UserRole.MODERATOR: 2,
            UserRole.ADMIN: 3
        }
        return role_level[self.role] >= role_level[required_role]