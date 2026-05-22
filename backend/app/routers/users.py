from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import User, UserCreate, UserUpdate
from app import crud, auth

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Получить список пользователей (только admin)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Получить пользователя по ID (только admin)"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Обновить пользователя (только admin)"""
    db_user = crud.update_user(db, user_id=user_id, user_update=user_update.dict(exclude_unset=True))
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Удалить пользователя (только admin)"""
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.get("/me", response_model=User)
def read_current_user(
    current_user: User = Depends(auth.get_current_active_user)
):
    """Получить текущего пользователя"""
    return current_user