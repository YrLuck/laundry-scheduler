from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
from app.models import Machine, Booking, User, Role, Permission, role_permissions
from app.schemas import MachineCreate, BookingCreate, UserCreate, RoleCreate, PermissionCreate

# ==================== PERMISSIONS ====================

def get_permission(db: Session, permission_id: int):
    return db.query(Permission).filter(Permission.id == permission_id).first()

def get_permission_by_name(db: Session, name: str):
    return db.query(Permission).filter(Permission.name == name).first()

def get_permissions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Permission).offset(skip).limit(limit).all()

def create_permission(db: Session, permission: PermissionCreate):
    db_permission = Permission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def delete_permission(db: Session, permission_id: int):
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        return None
    db.delete(permission)
    db.commit()
    return permission

# ==================== ROLES ====================

def get_role(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()

def get_role_by_name(db: Session, name: str):
    return db.query(Role).filter(Role.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Role).offset(skip).limit(limit).all()

def create_role(db: Session, role: RoleCreate):
    db_role = Role(name=role.name, description=role.description)
    if role.permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(role.permission_ids)).all()
        db_role.permissions = permissions
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, role_id: int, role_update: dict):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return None
    
    for field, value in role_update.items():
        if field != "permission_ids" and value is not None:
            setattr(role, field, value)
    
    if "permission_ids" in role_update and role_update["permission_ids"] is not None:
        permissions = db.query(Permission).filter(Permission.id.in_(role_update["permission_ids"])).all()
        role.permissions = permissions
    
    db.commit()
    db.refresh(role)
    return role

def delete_role(db: Session, role_id: int):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return None
    db.delete(role)
    db.commit()
    return role

def assign_role_to_user(db: Session, user_id: int, role_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if not user or not role:
        return None
    user.role_id = role_id
    db.commit()
    db.refresh(user)
    return user

def user_has_permission(db: Session, user_id: int, permission_name: str) -> bool:
    """Проверяет наличие разрешения у пользователя через его роль."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.role:
        return False

    # Admin обходит проверку разрешений — у него полный доступ
    if user.role.name == "admin":
        return True
    
    for permission in user.role.permissions:
        if permission.name == permission_name:
            return True
    return False

def get_user_permissions(db: Session, user_id: int) -> list:
    """Получает список разрешений пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.role:
        return []
    return [p.name for p in user.role.permissions]

# ==================== MACHINES ====================

def get_machine(db: Session, machine_id: int):
    return db.query(Machine).filter(Machine.id == machine_id).first()

def get_machines(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    machine_type: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
):
    """Получение списка машин с фильтрацией, поиском и сортировкой"""
    query = db.query(Machine)
    
    # Поиск по названию
    if search:
        query = query.filter(Machine.name.ilike(f"%{search}%"))
    
    # Фильтр по типу
    if machine_type:
        query = query.filter(Machine.type == machine_type)
    
    # Фильтр по статусу
    if status:
        query = query.filter(Machine.status == status)
    
    # Сортировка
    if sort_by:
        sort_column = getattr(Machine, sort_by, None)
        if sort_column:
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
    
    return query.offset(skip).limit(limit).all()

def count_machines(
    db: Session,
    search: Optional[str] = None,
    machine_type: Optional[str] = None,
    status: Optional[str] = None
) -> int:
    """Подсчет количества машин с учетом фильтров"""
    query = db.query(Machine)
    
    if search:
        query = query.filter(Machine.name.ilike(f"%{search}%"))
    if machine_type:
        query = query.filter(Machine.type == machine_type)
    if status:
        query = query.filter(Machine.status == status)
    
    return query.count()

def create_machine(db: Session, machine: MachineCreate):
    db_machine = Machine(**machine.dict())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

def update_machine(db: Session, machine_id: int, machine_update: dict):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        return None
    for field, value in machine_update.items():
        if value is not None:
            setattr(machine, field, value)
    db.commit()
    db.refresh(machine)
    return machine

def delete_machine(db: Session, machine_id: int):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        return None
    db.delete(machine)
    db.commit()
    return machine

# ==================== BOOKINGS ====================

def get_booking(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_bookings(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    machine_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
):
    """Получение списка бронирований с фильтрацией"""
    query = db.query(Booking)
    
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    if machine_id:
        query = query.filter(Booking.machine_id == machine_id)
    if status:
        query = query.filter(Booking.status == status)
    if start_date:
        query = query.filter(Booking.start_time >= start_date)
    if end_date:
        query = query.filter(Booking.end_time <= end_date)
    
    if sort_by:
        sort_column = getattr(Booking, sort_by, None)
        if sort_column:
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
    
    return query.offset(skip).limit(limit).all()

def count_bookings(
    db: Session,
    user_id: Optional[int] = None,
    machine_id: Optional[int] = None,
    status: Optional[str] = None
) -> int:
    """Подсчет количества бронирований с учетом фильтров"""
    query = db.query(Booking)
    
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    if machine_id:
        query = query.filter(Booking.machine_id == machine_id)
    if status:
        query = query.filter(Booking.status == status)
    
    return query.count()

def get_user_bookings(db: Session, user_id: int = None, user_name: str = None):
    if user_id:
        return db.query(Booking).filter(Booking.user_id == user_id).all()
    return db.query(Booking).filter(Booking.user_name == user_name).all()

def create_booking(db: Session, booking: BookingCreate, user_id: int = None, user_name: str = None):
    machine = get_machine(db, booking.machine_id)
    if not machine:
        return None

    # Проверка пересечений времени: новый слот не должен перекрываться ни с каким активным бронированием
    conflicting_booking = db.query(Booking).filter(
        Booking.machine_id == booking.machine_id,
        Booking.status == "active",
        or_(
            and_(Booking.start_time <= booking.start_time, Booking.end_time > booking.start_time),
            and_(Booking.start_time < booking.end_time, Booking.end_time >= booking.end_time),
            and_(Booking.start_time >= booking.start_time, Booking.end_time <= booking.end_time)
        )
    ).first()

    if conflicting_booking:
        return None

    db_booking = Booking(**booking.dict(), user_id=user_id, user_name=user_name)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def cancel_booking(db: Session, booking_id: int):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking:
        booking.status = "cancelled"
        db.commit()
        db.refresh(booking)
    return booking

def get_available_time_slots(db: Session, machine_id: int, date: datetime):
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    bookings = db.query(Booking).filter(
        Booking.machine_id == machine_id,
        Booking.status == "active",
        Booking.start_time >= start_of_day,
        Booking.end_time <= end_of_day
    ).order_by(Booking.start_time).all()

    # Генерируем часовые слоты с 8:00 до 22:00 и помечаем занятые
    time_slots = []
    current_time = start_of_day.replace(hour=8, minute=0)
    end_time = start_of_day.replace(hour=22, minute=0)

    while current_time < end_time:
        slot_end = current_time + timedelta(hours=1)

        # Check if this slot is available
        is_available = True
        for booking in bookings:
            if (current_time < booking.end_time and slot_end > booking.start_time):
                is_available = False
                break

        if is_available:
            time_slots.append({
                "start_time": current_time,
                "end_time": slot_end,
                "available": True
            })
        else:
            time_slots.append({
                "start_time": current_time,
                "end_time": slot_end,
                "available": False,
                "booked_by": next((b.user_name for b in bookings if
                                 b.start_time <= current_time and b.end_time >= slot_end), None)
            })

        current_time = slot_end

    return time_slots

def update_booking(db: Session, booking_id: int, booking_update: dict):
    """Update a booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None

    # Update only the fields that are provided
    for field, value in booking_update.items():
        if value is not None:
            setattr(booking, field, value)

    db.commit()
    db.refresh(booking)
    return booking

def delete_booking(db: Session, booking_id: int):
    """Delete a booking completely"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None

    db.delete(booking)
    db.commit()
    return booking

# ==================== USERS ====================

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate, hashed_password: str, role_id: int = None):
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role_id=role_id,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Update only the fields that are provided
    for field, value in user_update.items():
        if value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    db.delete(user)
    db.commit()
    return user