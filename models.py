from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column, Mapped
from sqlalchemy import ForeignKey, String, Float, Integer, DateTime, Boolean, Text
from datetime import datetime
from typing import Optional, List

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # Хеш пароля
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Связи
    messages: Mapped[List['Messages']] = relationship('Messages', back_populates='sender')
    chats: Mapped[List['Chats']] = relationship(
        'Chats', 
        secondary='chat_participants',
        back_populates='participants'
    )

class Chats(Base):
    __tablename__ = 'chats'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Для групповых чатов
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    messages: Mapped[List['Messages']] = relationship('Messages', back_populates='chat')
    participants: Mapped[List['Users']] = relationship(
        'Users', 
        secondary='chat_participants',
        back_populates='chats'
    )

class Messages(Base):
    __tablename__ = 'messages'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'), nullable=False, index=True)
    
    # Связи
    sender: Mapped['Users'] = relationship('Users', back_populates='messages')
    chat: Mapped['Chats'] = relationship('Chats', back_populates='messages')

class ChatParticipants(Base):
    __tablename__ = 'chat_participants'
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey('chats.id'), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
'''
Пользователи: хранят логин, никнейм и хеш пароля
Чаты: могут быть личными (is_group=False) или групповыми
Сообщения: привязаны к отправителю и чату
Связь многие-ко-многим: через таблицу chat_participants
Индексы: для быстрого поиска сообщений по чату и времени

Эта структура поддерживает:
Личные переписки
Групповые чаты
Историю сообщений
Отметки о прочтении (можно расширить)
Временные метки
'''

