from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from services.file_service import FileService
from models.user import Users

router = APIRouter()

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = FileService(db)
    return await service.upload_image(file)

@router.post("/cleanup/images")
async def cleanup_old_images(
    days: int = 7,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    
    service = FileService(db)
    return service.cleanup_old_images(days)