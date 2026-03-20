from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.dependencies import get_current_user
from models.user import Users

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request, user: Users = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/messager", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/messager", response_class=HTMLResponse)
async def messager_page(request: Request, user: Users = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "messager.html", 
        {
            "request": request, 
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "profileimage": user.profileimage
        }
    )

@router.get("/nas", response_class=HTMLResponse)
async def nas_page(request: Request, user: Users = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(
        "nas.html", 
        {
            "request": request, 
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname
        }
    )