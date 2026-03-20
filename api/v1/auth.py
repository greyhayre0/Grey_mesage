from fastapi import APIRouter, Depends, HTTPException, Request, Cookie
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.security import delete_session
from core.dependencies import get_current_user
from services.auth_service import AuthService
from schemas.user import UserAuth

from pydantic import ValidationError

router = APIRouter()

@router.post("/login")
async def login(user_data: UserAuth, db: Session = Depends(get_db)):
    """
    Вход пользователя
    
    - **username**: логин (5-50 символов, только латиница, цифры, _)
    - **password**: пароль (8-100 символов, заглавные, строчные, цифры, спецсимволы)
    """
    try:
        service = AuthService(db)
        result = service.authenticate(user_data.username, user_data.password)
    
        if not result:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
        session_token, user = result
    
        response = JSONResponse(
            status_code=200,
            content={"message": "Успешный вход!", "redirect": "/messager"}
        )
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=86400,
            expires=86400,
            secure=False,  # В продакшене изменить на True
            samesite="lax"
        )
    
        return response
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = error['loc'][0]
            msg = error['msg']
            errors.append(f"{field}: {msg}")
        
        raise HTTPException(
            status_code=422,
            detail={"errors": errors}
        )

@router.post("/register")
async def register(user_data: UserAuth, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    
    - **username**: логин (5-50 символов, только латиница, цифры, _)
    - **password**: пароль (8-100 символов, заглавные, строчные, цифры, спецсимволы)
    """
    try:
        service = AuthService(db)
        result = service.register(user_data.username, user_data.password)
        
        if not result:
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
        
        session_token, user = result
        
        response = JSONResponse(
            status_code=200,
            content={"message": "Регистрация успешна!", "redirect": "/messager"}
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
    
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = error['loc'][0]
            msg = error['msg']
            errors.append(f"{field}: {msg}")
        
        raise HTTPException(
            status_code=422,
            detail={"errors": errors}
        )

@router.post("/logout")
async def logout(session_token: Optional[str] = Cookie(None)):
    """Выход из системы"""
    if session_token:
        delete_session(session_token)
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_token")
    return response