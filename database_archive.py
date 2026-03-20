from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Подключение к базе данных (здесь пример для SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # файл базы данных в текущей папке

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}  # для SQLite
)

# Создаем класс Base для моделей
Base = declarative_base()

# Сессия для взаимодействия с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)