from fastapi import FastAPI,  Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from sqlalchemy.orm import Session

from core.database import engine, Base, get_db
from api.v1 import auth, chats, messages, users, uploads, pages
from websocket.connection_manager import router as ws_router
from utils.cleanup import delete_old_messages
from core.dependencies import get_current_user

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание приложения
app = FastAPI(title="Messenger API")

# Шаблоны и статика
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Создание таблиц базы данных
Base.metadata.create_all(bind=engine)

# Подключение роутеров API
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(chats.router, prefix="/api/v1", tags=["chats"])
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(uploads.router, prefix="/api/v1", tags=["uploads"])

app.include_router(pages.router)
# Подключение WebSocket
app.include_router(ws_router)

# Дополнительный эндпоинт для ручной очистки (из монолита)
@app.post("/api/cleanup")
async def cleanup_old_messages_endpoint(
    days: int = 7,
    db: Session = Depends(get_db),
    user: users = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    count = delete_old_messages(db, days)
    return {"deleted_count": count, "older_than_days": days}

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск очистки старых сообщений...")
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        delete_old_messages(db)
    finally:
        db.close()