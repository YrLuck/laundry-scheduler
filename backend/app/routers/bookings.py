from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.schemas import Booking, BookingCreate, BookingUpdate, BookingWithMachine, User
from app import crud, auth

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=Booking)
def create_booking(
    booking: BookingCreate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать бронирование от имени текущего пользователя"""
    db_booking = crud.create_booking(
        db=db,
        booking=booking,
        user_id=current_user.id,
        user_name=current_user.username
    )

    if db_booking is None:
        raise HTTPException(status_code=400, detail="Booking conflict or machine not found")
    return db_booking

@router.get("/", response_model=list[BookingWithMachine])
def read_bookings(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    user_id: Optional[int] = Query(None, description="Фильтр по пользователю"),
    machine_id: Optional[int] = Query(None, description="Фильтр по машине"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    start_date: Optional[datetime] = Query(None, description="Фильтр по дате начала"),
    end_date: Optional[datetime] = Query(None, description="Фильтр по дате окончания"),
    sort_by: Optional[str] = Query(None, description="Поле для сортировки"),
    sort_order: str = Query("asc", description="Порядок сортировки"),
    db: Session = Depends(get_db)
):
    """
    Получить все бронирования с фильтрацией и пагинацией.
    
    Параметры:
    - skip, limit: пагинация
    - user_id: фильтр по ID пользователя
    - machine_id: фильтр по ID машины
    - status: фильтр по статусу (active/completed/cancelled)
    - start_date, end_date: фильтр по диапазону дат
    - sort_by: поле для сортировки (start_time, end_time, created_at)
    - sort_order: порядок сортировки (asc/desc)
    """
    bookings = crud.get_bookings(
        db, skip=skip, limit=limit,
        user_id=user_id,
        machine_id=machine_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return bookings

@router.get("/count")
def get_bookings_count(
    user_id: Optional[int] = Query(None, description="Фильтр по пользователю"),
    machine_id: Optional[int] = Query(None, description="Фильтр по машине"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    """Получить общее количество бронирований с учетом фильтров"""
    total = crud.count_bookings(
        db,
        user_id=user_id,
        machine_id=machine_id,
        status=status
    )
    return {"total": total}

@router.get("/my-bookings", response_model=list[BookingWithMachine])
def read_my_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить мои бронирования с пагинацией"""
    return crud.get_bookings(
        db, skip=skip, limit=limit,
        user_id=current_user.id,
        status=status,
        sort_by="start_time",
        sort_order="desc"
    )

@router.get("/user/{user_id}", response_model=list[BookingWithMachine])
def read_user_bookings(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить бронирования пользователя (только свои или admin)"""
    if current_user.id != user_id:
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_bookings(db, skip=skip, limit=limit, user_id=user_id)

@router.get("/{booking_id}", response_model=BookingWithMachine)
def get_booking(
    booking_id: int,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить бронирование по ID"""
    db_booking = crud.get_booking(db, booking_id=booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.user_id != current_user.id:
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return db_booking

@router.post("/{booking_id}/cancel", response_model=Booking)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отменить бронирование (только владелец или admin)"""
    db_booking = crud.get_booking(db, booking_id=booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.user_id != current_user.id:
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.cancel_booking(db, booking_id=booking_id)

@router.put("/{booking_id}", response_model=Booking)
def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить бронирование (только владелец или admin)"""
    db_booking = crud.get_booking(db, booking_id=booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.user_id != current_user.id:
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.update_booking(db, booking_id=booking_id, booking_update=booking_update.dict(exclude_unset=True))

@router.delete("/{booking_id}", response_model=Booking)
def delete_booking(
    booking_id: int,
    current_user: User = Depends(auth.require_permission("bookings:delete")),
    db: Session = Depends(get_db)
):
    """Удалить бронирование (требуется разрешение bookings:delete)"""
    db_booking = crud.delete_booking(db, booking_id=booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking