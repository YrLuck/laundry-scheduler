"""
Сервисный слой для аутентификации и авторизации.
Использует Repository паттерн для доступа к данным.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import bcrypt

from app.repositories import UserRepository
from app.schemas import UserCreate, TokenData


class AuthService:
    """Сервис аутентификации: хеширование паролей, выдача и валидация JWT-токенов."""

    # Секрет читается из env — в docker-compose задаётся через переменную SECRET_KEY
    SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30   # время жизни access-токена
    REFRESH_TOKEN_EXPIRE_DAYS = 7      # время жизни refresh-токена
    
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """
        Аутентификация пользователя.
        Возвращает данные пользователя если успешна, иначе None.
        """
        user = self.user_repo.get_by_username(username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role
        }
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание access токена"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
    
    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание refresh токена"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
    
    def create_token_pair(self, username: str) -> dict:
        # Оба токена кладём в payload поле "sub" (subject) — стандарт JWT
        access_token = self.create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = self.create_refresh_token(
            data={"sub": username},
            expires_delta=timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def validate_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """Декодирует JWT и возвращает TokenData; None если токен невалиден или не того типа."""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: str = payload.get("sub")
            token_payload_type: str = payload.get("type")

            # Проверяем что тип токена совпадает (access нельзя использовать как refresh)
            if username is None or token_payload_type != token_type:
                return None
            
            return TokenData(username=username)
        except JWTError:
            return None
    
    def refresh_tokens(self, refresh_token: str) -> Optional[dict]:
        """
        Обновление пары токенов по refresh токену.
        Возвращает новую пару токенов или None если refresh невалиден.
        """
        token_data = self.validate_token(refresh_token, token_type="refresh")
        if not token_data:
            return None
        
        user = self.user_repo.get_by_username(token_data.username)
        if not user or not user.is_active:
            return None
        
        return self.create_token_pair(user.username)
    
    def register_user(self, user_data: UserCreate) -> dict:
        """
        Регистрация нового пользователя.
        Возвращает данные созданного пользователя.
        """
        # Проверка существующего пользователя
        existing = self.user_repo.get_by_username(user_data.username)
        if existing:
            raise ValueError("Username already registered")
        
        # Проверка существующего email
        existing_by_email = self.user_repo.get_by_email(user_data.email)
        if existing_by_email:
            raise ValueError("Email already registered")
        
        # Хеширование пароля и создание пользователя
        hashed_password = self.get_password_hash(user_data.password)
        
        # Получаем роль "user" по умолчанию
        from app.repositories import RoleRepository
        from sqlalchemy.orm import Session
        
        user = self.user_repo.create(user_data, hashed_password)
        return user
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Проверка наличия разрешения у пользователя"""
        return self.user_repo.has_permission(user_id, permission)
    
    def get_user_permissions(self, user_id: int) -> list:
        """Получение списка разрешений пользователя"""
        return self.user_repo.get_permissions(user_id)
