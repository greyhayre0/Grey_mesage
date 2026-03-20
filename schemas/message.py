from pydantic import BaseModel
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    chat_id: int

class MessageResponse(BaseModel):
    id: int
    content: str
    timestamp: datetime
    sender_id: int
    sender_name: str
    sender_avatar: str
    is_mine: bool
    is_read: bool