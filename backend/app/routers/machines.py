from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas import Machine, MachineCreate, User
from app import crud, auth

router = APIRouter(prefix="/machines", tags=["machines"])

@router.post("/", response_model=Machine)
def create_machine(
    machine: MachineCreate,
    current_user: User = Depends(auth.require_permission("machines:create")),
    db: Session = Depends(get_db)
):
    """Создать машину (требуется разрешение machines:create)"""
    return crud.create_machine(db=db, machine=machine)

@router.get("/", response_model=list[Machine])
def read_machines(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    machine_type: Optional[str] = Query(None, description="Фильтр по типу (washer/dryer)"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    sort_by: Optional[str] = Query(None, description="Поле для сортировки"),
    sort_order: str = Query("asc", description="Порядок сортировки (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех машин с фильтрацией, поиском, сортировкой и пагинацией.
    
    Параметры:
    - skip: количество пропускаемых записей (пагинация)
    - limit: количество возвращаемых записей (пагинация)
    - search: поиск по названию машины
    - machine_type: фильтр по типу (washer/dryer)
    - status: фильтр по статусу (available/in_use/maintenance)
    - sort_by: поле для сортировки (name, type, status, created_at)
    - sort_order: порядок сортировки (asc/desc)
    """
    machines = crud.get_machines(
        db, skip=skip, limit=limit,
        search=search,
        machine_type=machine_type,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return machines

@router.get("/count")
def get_machines_count(
    search: Optional[str] = Query(None, description="Поиск по названию"),
    machine_type: Optional[str] = Query(None, description="Фильтр по типу"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    """Получить общее количество машин с учетом фильтров"""
    total = crud.count_machines(
        db,
        search=search,
        machine_type=machine_type,
        status=status
    )
    return {"total": total}

@router.get("/{machine_id}", response_model=Machine)
def read_machine(
    machine_id: int,
    db: Session = Depends(get_db)
):
    """Получить машину по ID (публично)"""
    db_machine = crud.get_machine(db, machine_id=machine_id)
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.get("/{machine_id}/time-slots")
def get_machine_time_slots(
    machine_id: int,
    date: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить доступные временные слоты для машины"""
    from datetime import datetime
    try:
        target_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    return crud.get_available_time_slots(db, machine_id, target_date)

@router.put("/{machine_id}", response_model=Machine)
def update_machine(
    machine_id: int,
    machine_update: MachineCreate,
    current_user: User = Depends(auth.require_permission("machines:update")),
    db: Session = Depends(get_db)
):
    """Обновить машину (требуется разрешение machines:update)"""
    db_machine = crud.update_machine(db, machine_id=machine_id, machine_update=machine_update.dict())
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return db_machine

@router.delete("/{machine_id}")
def delete_machine(
    machine_id: int,
    current_user: User = Depends(auth.require_permission("machines:delete")),
    db: Session = Depends(get_db)
):
    """Удалить машину (требуется разрешение machines:delete)"""
    db_machine = crud.delete_machine(db, machine_id=machine_id)
    if db_machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": "Machine deleted successfully"}