from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
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

# Импортируем ваши модели
from models import Base, Users, Chats, Messages, ChatParticipants

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./your_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Хранилище сессий (в реальном проекте используйте Redis или БД)
sessions = {}

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
        {"request": request, "username": user.username}
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

# Пример защищенного API маршрута
@app.get("/api/user/info")
async def get_user_info(user: Users = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "created_at": user.created_at,
        "last_seen": user.last_seen
    }

# Для отладки - посмотреть активные сессии
@app.get("/debug/sessions")
async def debug_sessions():
    return {
        "active_sessions": len(sessions),
        "sessions": [
            {
                "username": data['username'],
                "created_at": data['created_at'],
                "age_seconds": (datetime.utcnow() - data['created_at']).seconds
            }
            for data in sessions.values()
        ]
    }