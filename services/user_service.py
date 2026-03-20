from sqlalchemy.orm import Session

from models.user import Users

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_users(self, query: str, current_user_id: int, limit: int = 10):
        users = self.db.query(Users).filter(
            Users.username.contains(query),
            Users.id != current_user_id
        ).limit(limit).all()
        
        return [
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname
            }
            for u in users
        ]
    
    def update_avatar(self, user: Users, avatar_url: str):
        if not avatar_url:
            return {"success": False, "error": "URL не может быть пустым"}
        
        user.profileimage = avatar_url
        self.db.commit()
        
        return {"success": True}
    
    def update_nickname(self, user: Users, nickname: str):
        if not nickname or not nickname.strip():
            return {"success": False, "error": "Никнейм не может быть пустым"}
        
        user.nickname = nickname.strip()
        self.db.commit()
        
        return {"success": True}
    
    def get_user_info(self, user: Users):
        return {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "created_at": user.created_at.isoformat(),
            "last_seen": user.last_seen.isoformat() if user.last_seen else None
        }