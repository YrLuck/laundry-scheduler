from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import Role, RoleCreate, Permission, PermissionCreate, User
from app import crud, auth

router = APIRouter(prefix="/rbac", tags=["rbac"])

# ==================== PERMISSIONS ====================

@router.post("/permissions/", response_model=Permission)
def create_permission(
    permission: PermissionCreate,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Создать разрешение (только admin)"""
    # Check if permission already exists
    existing = crud.get_permission_by_name(db, name=permission.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists"
        )
    return crud.create_permission(db=db, permission=permission)


@router.get("/permissions/", response_model=List[Permission])
def get_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список всех разрешений"""
    return crud.get_permissions(db, skip=skip, limit=limit)


@router.get("/permissions/{permission_id}", response_model=Permission)
def get_permission(
    permission_id: int,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить разрешение по ID"""
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return db_permission


@router.delete("/permissions/{permission_id}")
def delete_permission(
    permission_id: int,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Удалить разрешение (только admin)"""
    db_permission = crud.delete_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission deleted successfully"}


# ==================== ROLES ====================

@router.post("/roles/", response_model=Role)
def create_role(
    role: RoleCreate,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Создать роль с разрешениями (только admin)"""
    # Check if role already exists
    existing = crud.get_role_by_name(db, name=role.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )
    return crud.create_role(db=db, role=role)


@router.get("/roles/", response_model=List[Role])
def get_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список всех ролей"""
    return crud.get_roles(db, skip=skip, limit=limit)


@router.get("/roles/{role_id}", response_model=Role)
def get_role(
    role_id: int,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить роль по ID"""
    db_role = crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role


@router.put("/roles/{role_id}", response_model=Role)
def update_role(
    role_id: int,
    role_update: RoleCreate,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Обновить роль (только admin)"""
    db_role = crud.update_role(db, role_id=role_id, role_update=role_update.dict())
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Удалить роль (только admin)"""
    db_role = crud.delete_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}


# ==================== USER ROLES ====================

@router.post("/users/{user_id}/assign-role/{role_id}")
def assign_role_to_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Назначить роль пользователю (только admin)"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_role = crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return crud.assign_role_to_user(db, user_id=user_id, role_id=role_id)


@router.get("/users/me/permissions", response_model=List[str])
def get_my_permissions(
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить список разрешений текущего пользователя"""
    return crud.get_user_permissions(db, user_id=current_user.id)


@router.get("/users/{user_id}/permissions", response_model=List[str])
def get_user_permissions(
    user_id: int,
    current_user: User = Depends(auth.require_role("admin")),
    db: Session = Depends(get_db)
):
    """Получить разрешения пользователя (только admin)"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_permissions(db, user_id=user_id)
