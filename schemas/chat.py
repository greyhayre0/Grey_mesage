from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatCreate(BaseModel):
    name: Optional[str] = None
    participant_ids: List[int]

class ChatResponse(BaseModel):
    id: int
    name: Optional[str]
    profileimage: str
    is_group: bool
    last_message: Optional[str]
    last_message_time: Optional[datetime]
    unread_count: int
    created_at: datetime