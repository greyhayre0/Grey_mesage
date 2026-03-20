from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

from core.security import get_session

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, chat_id: int):
        if chat_id in self.active_connections:
            if websocket in self.active_connections[chat_id]:
                self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
    
    def disconnect_chat(self, chat_id: int):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                try:
                    connection.close()
                except:
                    pass
            del self.active_connections[chat_id]
    
    async def broadcast_to_chat(self, chat_id: int, message: dict, exclude=None):
        if chat_id not in self.active_connections:
            return
        
        for connection in self.active_connections[chat_id]:
            if exclude and connection == exclude:
                continue
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    chat_id: int
):
    cookies = websocket.cookies
    session_token = cookies.get("session_token")
    
    if not session_token or not get_session(session_token):
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket, chat_id)
    
    try:
        while True:
            await websocket.receive_text()  # Просто поддерживаем соединение
            # Сообщения отправляются через REST API
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)