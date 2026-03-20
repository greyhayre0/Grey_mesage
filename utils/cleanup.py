from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from models.message import Messages
from core.config import settings

logger = logging.getLogger(__name__)

def delete_old_messages(db: Session, days: int = None):
    """Удаляет сообщения старше указанного количества дней"""
    if days is None:
        days = settings.MESSAGES_RETENTION_DAYS
    
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

# Алиас для обратной совместимости
cleanup_old_messages = delete_old_messages