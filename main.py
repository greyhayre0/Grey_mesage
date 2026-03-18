from fastapi import FastAPI, Request, HTTPException, Depends, Cookie, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import bcrypt
import secrets
from typing import Optional
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import logging
import json

# Импортируем ваши модели
from models import Base, Users, Chats, Messages, ChatParticipants

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./your_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Хранилище сессий и WebSocket (в реальном проекте используйте Redis или БД)
sessions = {}
active_connections = {}
# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Модель данных
class UserAuth(BaseModel):
    username: str
    password: str

class MessageCreate(BaseModel):
    content: str
    chat_id: int

class ChatCreate(BaseModel):
    name: Optional[str] = None
    participant_ids: List[int]

# Функция для проверки авторизации
def get_current_user(session_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not session_token or session_token not in sessions:
        return None
    
    session_data = sessions[session_token]
    # Проверяем, не истекла ли сессия (24 часа)
    if datetime.utcnow() - session_data['created_at'] > timedelta(hours=24):
        del sessions[session_token]
        return None
    
    # Получаем пользователя из БД
    user = db.query(Users).filter(Users.id == session_data['user_id']).first()
    return user

# Функция для очистки старых сообщений
def delete_old_messages(db: Session, days: int = 7):
    """Удаляет сообщения старше указанного количества дней"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Находим старые сообщения
        old_messages = db.query(Messages).filter(
            Messages.timestamp < cutoff_date
        ).all()
        
        count = len(old_messages)
        
        # Удаляем их
        for message in old_messages:
            db.delete(message)
        
        db.commit()
        
        if count > 0:
            logger.info(f"Удалено {count} старых сообщений (старше {days} дней)")
        
        return count
    except Exception as e:
        logger.error(f"Ошибка при удалении старых сообщений: {e}")
        db.rollback()
        return 0

# Запускаем очистку старых сообщений при старте
@app.on_event("startup")
async def startup_event():
    logger.info("Запуск очистки старых сообщений...")
    db = SessionLocal()
    try:
        delete_old_messages(db)
    finally:
        db.close()


# Страница логина (доступна всем)
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, user: Users = Depends(get_current_user)):
    # Если пользователь уже авторизован, редиректим на мессенджер
    if user:
        return RedirectResponse(url="/messager", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

# Защищенный маршрут - только для авторизованных
@app.get("/messager", response_class=HTMLResponse)
async def messager(request: Request, user: Users = Depends(get_current_user)):
    if not user:
        # Не авторизован - редирект на логин
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "messager.html", 
        {
            "request": request, 
            "user_id": user.id,           # Добавлено
            "username": user.username,     # Добавлено
            "nickname": user.nickname,      # Добавлено
            "profileimage": user.profileimage      # Добавлено
        }
    )

# API для входа
@app.post("/login")
async def login(user_data: UserAuth, db: Session = Depends(get_db)):
    try:
        # Ищем пользователя
        user = db.query(Users).filter(Users.username == user_data.username).first()
        
        if not user or not bcrypt.checkpw(user_data.password.encode('utf-8'), user.password.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        
        # Обновляем last_seen
        user.last_seen = datetime.utcnow()
        db.commit()
        
        # Создаем сессию
        session_token = secrets.token_hex(32)
        sessions[session_token] = {
            'user_id': user.id,
            'username': user.username,
            'created_at': datetime.utcnow()
        }
        
        # Создаем ответ с редиректом и устанавливаем cookie
        response = JSONResponse(
            status_code=200,
            content={
                "message": "Успешный вход!",
                "redirect": "/messager"
            }
        )
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,  # Защита от XSS
            max_age=86400,  # 24 часа в секундах
            expires=86400,
            secure=False,  # В продакшене должно быть True (HTTPS)
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка при входе: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сервера")

# API для регистрации
@app.post("/register")
async def register(user_data: UserAuth, db: Session = Depends(get_db)):
    try:
        # Проверяем, существует ли пользователь
        existing_user = db.query(Users).filter(Users.username == user_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
        
        # Хешируем пароль
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
        
        # Создаем пользователя
        new_user = Users(
            username=user_data.username,
            nickname=user_data.username,
            password=hashed_password.decode('utf-8'),
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Создаем сессию для нового пользователя
        session_token = secrets.token_hex(32)
        sessions[session_token] = {
            'user_id': new_user.id,
            'username': new_user.username,
            'created_at': datetime.utcnow()
        }
        
        # Ответ с cookie
        response = JSONResponse(
            status_code=200,
            content={
                "message": "Регистрация успешна!",
                "redirect": "/messager"
            }
        )
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=86400,
            expires=86400,
            secure=False,
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка при регистрации: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка сервера")

# Выход из системы
@app.post("/logout")
async def logout(session_token: Optional[str] = Cookie(None)):
    if session_token and session_token in sessions:
        del sessions[session_token]
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_token")
    return response

@app.get("/api/chats")
async def get_user_chats(
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Получаем все чаты пользователя
    chats = db.query(Chats).join(
        ChatParticipants
    ).filter(
        ChatParticipants.user_id == user.id
    ).all()
    
    result = []
    for chat in chats:
        # Получаем последнее сообщение
        last_message = db.query(Messages).filter(
            Messages.chat_id == chat.id
        ).order_by(Messages.timestamp.desc()).first()
        
        # Получаем количество непрочитанных
        unread_count = db.query(Messages).filter(
            Messages.chat_id == chat.id,
            Messages.is_read == False,
            Messages.sender_id != user.id
        ).count()
        
        # Для личных чатов показываем имя собеседника
        chat_name = chat.name
        other_participant = None  # <-- Объявляем переменную ЗДЕСЬ
        
        if not chat.is_group and not chat_name:
            # Находим собеседника
            other_participant = db.query(Users).join(
                ChatParticipants
            ).filter(
                ChatParticipants.chat_id == chat.id,
                Users.id != user.id
            ).first()
            if other_participant:
                chat_name = other_participant.nickname
        
        # Определяем аватар
        if chat.is_group:
            profileimage = '/static/default-avatar.png'
        else:
            profileimage = other_participant.profileimage if other_participant else '/static/default-avatar.png'
        
        result.append({
            "id": chat.id,
            "name": chat_name or f"Чат {chat.id}",
            "profileimage": profileimage,  # <-- Используем profileimage
            "is_group": chat.is_group,
            "last_message": last_message.content if last_message else None,
            "last_message_time": last_message.timestamp.isoformat() if last_message else None,
            "unread_count": unread_count,
            "created_at": chat.created_at.isoformat()
        })
    
    return result

# API для получения сообщений чата (только за последнюю неделю)
@app.get("/api/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int,
    limit: int = 50,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Проверяем, является ли пользователь участником чата
    participant = db.query(ChatParticipants).filter(
        ChatParticipants.chat_id == chat_id,
        ChatParticipants.user_id == user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    
    # Получаем сообщения за последнюю неделю
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    messages = db.query(Messages).filter(
        Messages.chat_id == chat_id,
        Messages.timestamp >= week_ago  # Только за последнюю неделю
    ).order_by(Messages.timestamp.desc()).limit(limit).all()
    
    # Помечаем сообщения как прочитанные
    for msg in messages:
        if msg.sender_id != user.id and not msg.is_read:
            msg.is_read = True
    db.commit()
    
    return [
        {
            "id": msg.id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.nickname,
            "is_mine": msg.sender_id == user.id,
            "is_read": msg.is_read
        }
        for msg in messages
    ]

# API для отправки сообщения
@app.post("/api/messages")
async def send_message(
    message: MessageCreate,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Проверяем доступ к чату
    participant = db.query(ChatParticipants).filter(
        ChatParticipants.chat_id == message.chat_id,
        ChatParticipants.user_id == user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    
    # Создаем сообщение
    new_message = Messages(
        content=message.content,
        sender_id=user.id,
        chat_id=message.chat_id,
        timestamp=datetime.utcnow(),
        is_read=False
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Отправляем сообщение через WebSocket если есть подключение
    chat_connections = active_connections.get(message.chat_id, [])
    for connection in chat_connections:
        try:
            await connection.send_json({
                "type": "new_message",
                "message": {
                    "id": new_message.id,
                    "content": new_message.content,
                    "sender_id": new_message.sender_id,
                    "sender_name": user.nickname,
                    "timestamp": new_message.timestamp.isoformat(),
                    "chat_id": new_message.chat_id
                }
            })
        except:
            pass
    
    return {
        "id": new_message.id,
        "content": new_message.content,
        "timestamp": new_message.timestamp.isoformat(),
        "sender_id": new_message.sender_id,
        "sender_name": user.nickname
    }

# WebSocket для реального времени
@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    chat_id: int,
    db: Session = Depends(get_db)
):
    await websocket.accept()
    
    # Получаем токен из cookies
    cookies = websocket.cookies
    session_token = cookies.get("session_token")
    
    if not session_token or session_token not in sessions:
        await websocket.close(code=1008)
        return
    
    user_id = sessions[session_token]['user_id']
    
    # Добавляем соединение
    if chat_id not in active_connections:
        active_connections[chat_id] = []
    active_connections[chat_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Сохраняем сообщение в БД
            new_message = Messages(
                content=message_data['content'],
                sender_id=user_id,
                chat_id=chat_id,
                timestamp=datetime.utcnow(),
                is_read=False
            )
            
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            # Получаем информацию об отправителе
            sender = db.query(Users).filter(Users.id == user_id).first()
            
            # Отправляем всем в чате
            for connection in active_connections[chat_id]:
                if connection != websocket:  # Не отправляем отправителю
                    try:
                        await connection.send_json({
                            "type": "new_message",
                            "message": {
                                "id": new_message.id,
                                "content": new_message.content,
                                "sender_id": user_id,
                                "sender_name": sender.nickname if sender else "User",
                                "timestamp": new_message.timestamp.isoformat(),
                                "chat_id": chat_id
                            }
                        })
                    except:
                        pass
                        
    except WebSocketDisconnect:
        if chat_id in active_connections:
            active_connections[chat_id].remove(websocket)

# API для создания чата
@app.post("/api/chats")
async def create_chat(
    chat_data: ChatCreate,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    # Добавляем текущего пользователя в участники
    all_participants = list(set(chat_data.participant_ids + [user.id]))
    
    # Определяем, групповой ли чат
    is_group = len(all_participants) > 2
    
    new_chat = Chats(
        name=chat_data.name,
        is_group=is_group,
        created_at=datetime.utcnow()
    )
    
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    for participant_id in all_participants:
        participant = ChatParticipants(
            user_id=participant_id,
            chat_id=new_chat.id,
            joined_at=datetime.utcnow()
        )
        db.add(participant)
    
    db.commit()
    
    return {"id": new_chat.id, "name": new_chat.name}

# API для поиска пользователей
@app.get("/api/users/search")
async def search_users(
    query: str,
    limit: int = 10,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    users = db.query(Users).filter(
        Users.username.contains(query),
        Users.id != user.id  # Исключаем себя
    ).limit(limit).all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname
        }
        for u in users
    ]

# API для ручной очистки старых сообщений
@app.post("/api/cleanup")
async def cleanup_old_messages(
    days: int = 7,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    count = delete_old_messages(db, days)
    return {"deleted_count": count, "older_than_days": days}

# API для получения информации о пользователе
@app.get("/api/user/info")
async def get_user_info(user: Users = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "created_at": user.created_at.isoformat(),
        "last_seen": user.last_seen.isoformat() if user.last_seen else None
    }

@app.delete("/api/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    try:
        # Проверяем, является ли пользователь участником чата
        participant = db.query(ChatParticipants).filter(
            ChatParticipants.chat_id == chat_id,
            ChatParticipants.user_id == user.id
        ).first()
        
        if not participant:
            return {"success": False, "error": "Чат не найден или нет доступа"}
        
        # Удаляем все сообщения чата
        db.query(Messages).filter(Messages.chat_id == chat_id).delete()
        
        # Удаляем всех участников чата
        db.query(ChatParticipants).filter(ChatParticipants.chat_id == chat_id).delete()
        
        # Удаляем сам чат
        chat = db.query(Chats).filter(Chats.id == chat_id).first()
        if chat:
            db.delete(chat)
        
        db.commit()
        
        # Закрываем WebSocket соединения для этого чата
        if chat_id in active_connections:
            for connection in active_connections[chat_id]:
                try:
                    await connection.close()
                except:
                    pass
            del active_connections[chat_id]
        
        return {"success": True}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления чата {chat_id}: {e}")
        return {"success": False, "error": str(e)}

@app.post("/update-avatar")
async def update_avatar(
    request: Request,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    try:
        data = await request.json()
        new_avatar_url = data.get('profileimage')
        
        if not new_avatar_url:
            return {"success": False, "error": "URL не может быть пустым"}
        
        # Обновляем пользователя
        user.profileimage = new_avatar_url
        db.commit()
        
        return {"success": True}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    
@app.post("/api/update-nickname")
async def update_nickname(
    request: Request,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    try:
        data = await request.json()
        new_nickname = data.get('nickname')
        
        if not new_nickname or not new_nickname.strip():
            return {"success": False, "error": "Никнейм не может быть пустым"}
        
        # Обновляем пользователя
        user.nickname = new_nickname.strip()
        db.commit()
        
        return {"success": True}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
#################################################################################

@app.get("/nas", response_class=HTMLResponse)
async def messager(request: Request, user: Users = Depends(get_current_user)):
    if not user:
        # Не авторизован - редирект на логин
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "nas.html", 
        {
            "request": request, 
            "user_id": user.id,           # Добавлено
            "username": user.username,     # Добавлено
            "nickname": user.nickname      # Добавлено
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")