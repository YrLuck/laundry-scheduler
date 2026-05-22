from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
from app.repositories import UserRepository
from app.services import AuthService

# Берём конфиг токенов из AuthService, чтобы не дублировать константы
SECRET_KEY = AuthService.SECRET_KEY
ALGORITHM = AuthService.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = AuthService.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = AuthService.REFRESH_TOKEN_EXPIRE_DAYS

# HTTPBearer — схема для Swagger UI и извлечения токена из заголовка Authorization: Bearer
security_scheme = HTTPBearer()
# auto_error=False: не бросает 403 если токен отсутствует (для публичных endpoint'ов)
security_scheme_optional = HTTPBearer(auto_error=False)

# Dependency для получения AuthService
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    # Создаём AuthService с репозиторием — так зависимости тестируемы и подменяемы
    user_repo = UserRepository(db)
    return AuthService(user_repo)

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def authenticate_user(db: Session, username: str, password: str):
    """Аутентификация пользователя через сервис"""
    auth_service = get_auth_service(db)
    return auth_service.authenticate(username, password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-based access control
def require_role(required_role: str):
    """Dependency-фабрика: проверяет, что роль пользователя совпадает с required_role."""
    async def role_checker(current_user: schemas.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        # Admin — суперпользователь, проходит любую проверку роли
        if current_user.role and current_user.role.name == "admin":
            return current_user
        
        # Проверяем роль пользователя
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )
        
        if current_user.role.name != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role: {required_role}"
            )
        return current_user
    return role_checker

def require_permission(permission_name: str):
    """Dependency-фабрика: проверяет наличие конкретного permission у пользователя через его роль."""
    async def permission_checker(
        current_user: schemas.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        # Admin имеет все права
        if current_user.role and current_user.role.name == "admin":
            return current_user
        
        # Проверяем наличие разрешения
        has_permission = crud.user_has_permission(db, current_user.id, permission_name)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires permission: {permission_name}"
            )
        return current_user
    return permission_checker

def get_current_user_optional(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security_scheme_optional)):
    """
    Получает текущего пользователя, если токен предоставлен и валиден.
    Если токена нет - возвращает None (для публичных endpoint'ов с опциональной авторизацией).
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = crud.get_user_by_username(db, username=username)
        if user and user.is_active:
            return user
    except JWTError:
        pass
    
    return None