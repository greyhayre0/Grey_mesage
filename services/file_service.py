from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from PIL import Image
from datetime import datetime, timedelta
import shutil
import uuid
import os
import io
import logging

from core.config import settings
from models.message import Messages

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, db: Session):
        self.db = db
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    async def upload_image(self, file: UploadFile):
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        contents = await file.read()
        
        try:
            img = Image.open(io.BytesIO(contents))
            img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if not file_extension:
            file_extension = '.jpg'
            
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            file_extension = '.jpg'
            
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = settings.UPLOAD_DIR / unique_filename
        
        await file.seek(0)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        if file_extension not in ['.jpg', '.jpeg']:
            try:
                img = Image.open(file_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                
                jpeg_path = settings.UPLOAD_DIR / f"{uuid.uuid4()}.jpg"
                img.save(jpeg_path, 'JPEG', quality=85, optimize=True)
                
                file_path.unlink()
                file_path = jpeg_path
                unique_filename = jpeg_path.name
            except Exception as e:
                logger.error(f"Error converting image: {e}")
        
        file_url = f"/uploads/images/{unique_filename}"
        
        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "fileUrl": file_url,
            "size": file_path.stat().st_size,
            "content_type": file.content_type
        }
    
    def cleanup_old_images(self, days: int):
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0
        
        for file_path in settings.UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_ctime)
                
                if file_time < cutoff_date:
                    file_url = f"/uploads/images/{file_path.name}"
                    used_in_messages = self.db.query(Messages).filter(
                        Messages.content.contains(file_url)
                    ).first()
                    
                    if not used_in_messages:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old image: {file_path.name}")
        
        return {"deleted_count": deleted_count, "older_than_days": days}