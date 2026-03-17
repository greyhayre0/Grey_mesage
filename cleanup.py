import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Messages

logger = logging.getLogger(__name__)

def delete_old_messages(db: Session, days: int = 7):
    """Удаляет сообщения старше указанного количества дней"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_messages = db.query(Messages).filter(
            Messages.timestamp < cutoff_date
        ).all()
        
        count = len(old_messages)
        
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

def cleanup_task():
    """Функция для периодического запуска"""
    from main import SessionLocal
    db = SessionLocal()
    try:
        delete_old_messages(db)
    finally:
        db.close()