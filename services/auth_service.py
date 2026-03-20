from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Tuple
from datetime import datetime, timezone

from models.user import Users, UserRole
from core.security import hash_password, verify_password, create_session

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate(self, username: str, password: str) -> Optional[Tuple[str, Users]]:
        """
        Аутентификация пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            Tuple[session_token, user] или None если аутентификация не удалась
        """
        username = username.lower()
        user = self.db.query(Users).filter(Users.username == username).first()
        
        if not user or not verify_password(password, user.password):
            return None
        
        user.last_seen = datetime.now(timezone.utc)
        self.db.commit()
        
        session_token = create_session(user.id, user.username)
        return session_token, user
    
    def register(self, username: str, password: str) -> Optional[Tuple[str, Users]]:
        """
        Регистрация нового пользователя
        
        Args:
            username: Имя пользователя (уже должно быть провалидировано Pydantic)
            password: Пароль (уже должен быть провалидирован Pydantic)
            
        Returns:
            Tuple[session_token, user] или None если пользователь уже существует
        """
        username = username.lower()
        existing_user = self.db.query(Users).filter(Users.username == username).first()
        if existing_user:
            return None
        
        hashed_password = hash_password(password)
        
        # Определяем роль при регистрации
        is_first_user = self.db.query(Users).count() == 0
        role = UserRole.ADMIN if is_first_user else UserRole.USER
        
        # Создаем пользователя с ролью
        new_user = Users(
            username=username,
            nickname=username,
            password=hashed_password,
            role=role,  # ✅ Добавляем роль!
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        session_token = create_session(new_user.id, new_user.username)
        return session_token, new_user
    
    def update_user_role(self, user_id: int, new_role: UserRole, current_user: Users) -> bool:
        """
        Обновление роли пользователя (только для администраторов)
        
        Args:
            user_id: ID пользователя, которому меняем роль
            new_role: Новая роль
            current_user: Текущий пользователь (должен быть админом)
        
        Returns:
            bool: Успешно ли обновление
        """
        # Только админ может менять роли
        if not current_user.is_admin():
            return False
        
        # Нельзя изменить роль последнего админа
        if current_user.id == user_id and new_role != UserRole.ADMIN:
            admin_count = self.db.query(Users).filter(Users.role == UserRole.ADMIN).count()
            if admin_count <= 1:
                return False
        
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.role = new_role
        self.db.commit()
        return True
    
    def get_user_by_id(self, user_id: int) -> Optional[Users]:
        """Получение пользователя по ID"""
        return self.db.query(Users).filter(Users.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[Users]:
        """Получение пользователя по имени"""
        return self.db.query(Users).filter(Users.username == username.lower()).first()
    
    def update_last_seen(self, user_id: int) -> None:
        """Обновление времени последнего визита"""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_seen = datetime.now(timezone.utc)
            self.db.commit()