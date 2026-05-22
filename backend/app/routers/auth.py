from datetime import timedelta
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app import crud, schemas, auth
from app.database import get_db
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password and create the user, assigning the default 'user' role
    hashed_password = auth.get_password_hash(user.password)
    user_role = crud.get_role_by_name(db, "user")
    role_id = user_role.id if user_role else None
    db_user = crud.create_user(db, user=user, hashed_password=hashed_password, role_id=role_id)
    return db_user

@router.post("/login", response_model=schemas.Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Вход в систему.
    Возвращает пару access и refresh токенов.
    """
    auth_service = auth.get_auth_service(db)
    user_data = auth_service.authenticate(form_data.username, form_data.password)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создаем токены через сервис
    tokens = auth_service.create_token_pair(form_data.username)
    return tokens

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    """Получение текущего пользователя"""
    return current_user

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth.security_scheme),
    db: Session = Depends(get_db)
):
    """Обновление access токена с использованием refresh токена"""
    auth_service = auth.get_auth_service(db)
    token = credentials.credentials
    
    tokens = auth_service.refresh_tokens(token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return tokens

@router.post("/logout")
def logout_user(
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    """
    Выход из системы.
    На клиенте нужно очистить токены.
    """
    # В stateless JWT logout выполняется на клиенте (очистка токенов)
    # Здесь можно добавить логику отзыва токена (blacklist)
    return {"message": "Successfully logged out"}

# Development endpoint to create first admin user (should be removed in production)
@router.post("/create-admin", response_model=schemas.User)
def create_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Создание первого администратора (только для разработки!)"""
    # Check if admin user already exists
    admin_user = crud.get_user_by_username(db, username="admin")
    if admin_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists"
        )

    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password and create the admin user
    hashed_password = auth.get_password_hash(user.password)
    db_user = crud.create_user(db, user=user, hashed_password=hashed_password)
    
    # Назначаем роль admin (если существует)
    admin_role = crud.get_role_by_name(db, "admin")
    if admin_role:
        db_user.role_id = admin_role.id
        db.commit()
        db.refresh(db_user)
    return db_user