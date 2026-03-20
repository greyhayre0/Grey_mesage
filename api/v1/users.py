from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from services.user_service import UserService
from models.user import Users

router = APIRouter()

@router.get("/users/search")
async def search_users(
    query: str,
    limit: int = 10,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = UserService(db)
    return service.search_users(query, user.id, limit)

@router.get("/user/info")
async def get_user_info(user: Users = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = UserService(None)
    return service.get_user_info(user)

@router.post("/update-avatar")
async def update_avatar(
    request: Request,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = UserService(db)
    data = await request.json()
    return service.update_avatar(user, data.get('profileimage'))

@router.post("/update-nickname")
async def update_nickname(
    request: Request,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = UserService(db)
    data = await request.json()
    return service.update_nickname(user, data.get('nickname'))