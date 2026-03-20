from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from pywebpush import webpush, WebPushException

from core.database import get_db
from core.dependencies import get_current_user
from models.user import Users

router = APIRouter()

# Эти ключи нужно сгенерировать (выполни скрипт ниже один раз)
VAPID_PRIVATE_KEY = "YOUR_PRIVATE_KEY"
VAPID_PUBLIC_KEY = "YOUR_PUBLIC_KEY"
VAPID_CLAIMS = {
    "sub": "mailto:your-email@example.com"
}

@router.get("/push/public-key")
async def get_public_key():
    """Отдаем публичный ключ для браузера"""
    return {"public_key": VAPID_PUBLIC_KEY}

@router.post("/push/subscribe")
async def subscribe_to_push(
    subscription: dict,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """Сохраняем push-подписку пользователя"""
    current_user.push_subscription = json.dumps(subscription)
    db.commit()
    return {"status": "ok"}

def send_push_to_user(user: Users, title: str, body: str):
    """Отправить push-уведомление пользователю"""
    if not user.push_subscription:
        return False
    
    subscription = json.loads(user.push_subscription)
    
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        return True
    except WebPushException as e:
        print(f"Push error: {e}")
        return False