from pathlib import Path

class Settings:
    # База данных
    DATABASE_URL = "sqlite:///./your_database.db"
    
    # Безопасность
    SESSION_EXPIRE_HOURS = 24
    SESSION_EXPIRE_SECONDS = 86400
    
    # Очистка сообщений
    MESSAGES_RETENTION_DAYS = 7
    
    # Загрузка файлов
    UPLOAD_DIR = Path("uploads/images")
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # WebSocket
    WS_PING_INTERVAL = 30

settings = Settings()