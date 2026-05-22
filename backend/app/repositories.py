"""
Repository слой для работы с данными.
Изолирует работу с базой данных от бизнес-логики.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.models import Machine, Booking, User, Role, Permission
from app.schemas import (
    MachineCreate, BookingCreate, BookingUpdate,
    UserCreate, UserUpdate, RoleCreate, PermissionCreate
)


class BaseRepository:
    """Базовый репозиторий с общими методами"""
    
    def __init__(self, db: Session):
        self.db = db


class PermissionRepository(BaseRepository):
    """Репозиторий для работы с разрешениями"""
    
    def get(self, permission_id: int) -> Optional[Permission]:
        return self.db.query(Permission).filter(Permission.id == permission_id).first()
    
    def get_by_name(self, name: str) -> Optional[Permission]:
        return self.db.query(Permission).filter(Permission.name == name).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        return self.db.query(Permission).offset(skip).limit(limit).all()
    
    def create(self, permission: PermissionCreate) -> Permission:
        db_permission = Permission(**permission.dict())
        self.db.add(db_permission)
        self.db.commit()
        self.db.refresh(db_permission)
        return db_permission
    
    def delete(self, permission_id: int) -> Optional[Permission]:
        permission = self.get(permission_id)
        if permission:
            self.db.delete(permission)
            self.db.commit()
        return permission


class RoleRepository(BaseRepository):
    """Репозиторий для работы с ролями"""
    
    def get(self, role_id: int) -> Optional[Role]:
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_by_name(self, name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        return self.db.query(Role).offset(skip).limit(limit).all()
    
    def create(self, role: RoleCreate) -> Role:
        db_role = Role(name=role.name, description=role.description)
        if role.permission_ids:
            permissions = self.db.query(Permission).filter(
                Permission.id.in_(role.permission_ids)
            ).all()
            db_role.permissions = permissions
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role
    
    def update(self, role_id: int, role_update: dict) -> Optional[Role]:
        role = self.get(role_id)
        if not role:
            return None
        
        for field, value in role_update.items():
            if field != "permission_ids" and value is not None:
                setattr(role, field, value)
        
        if "permission_ids" in role_update and role_update["permission_ids"] is not None:
            permissions = self.db.query(Permission).filter(
                Permission.id.in_(role_update["permission_ids"])
            ).all()
            role.permissions = permissions
        
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def delete(self, role_id: int) -> Optional[Role]:
        role = self.get(role_id)
        if role:
            self.db.delete(role)
            self.db.commit()
        return role


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями"""
    
    def get(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def create(self, user: UserCreate, hashed_password: str, role_id: Optional[int] = None) -> User:
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role_id=role_id,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: int, user_update: dict) -> Optional[User]:
        user = self.get(user_id)
        if not user:
            return None
        
        for field, value in user_update.items():
            if value is not None:
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> Optional[User]:
        user = self.get(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
        return user
    
    def assign_role(self, user_id: int, role_id: int) -> Optional[User]:
        user = self.get(user_id)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not user or not role:
            return None
        user.role_id = role_id
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def has_permission(self, user_id: int, permission_name: str) -> bool:
        user = self.get(user_id)
        if not user or not user.role:
            return False
        
        if user.role.name == "admin":
            return True
        
        return any(p.name == permission_name for p in user.role.permissions)
    
    def get_permissions(self, user_id: int) -> List[str]:
        user = self.get(user_id)
        if not user or not user.role:
            return []
        return [p.name for p in user.role.permissions]


class MachineRepository(BaseRepository):
    """Репозиторий для работы с машинами"""
    
    def get(self, machine_id: int) -> Optional[Machine]:
        return self.db.query(Machine).filter(Machine.id == machine_id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        machine_type: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> List[Machine]:
        """
        Получение списка машин с фильтрацией, поиском и сортировкой.
        
        :param search: Поиск по названию
        :param machine_type: Фильтр по типу (washer/dryer)
        :param status: Фильтр по статусу
        :param sort_by: Поле для сортировки
        :param sort_order: Порядок сортировки (asc/desc)
        """
        query = self.db.query(Machine)
        
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
    
    def count(
        self,
        search: Optional[str] = None,
        machine_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Подсчет общего количества с учетом фильтров"""
        query = self.db.query(Machine)
        
        if search:
            query = query.filter(Machine.name.ilike(f"%{search}%"))
        if machine_type:
            query = query.filter(Machine.type == machine_type)
        if status:
            query = query.filter(Machine.status == status)
        
        return query.count()
    
    def create(self, machine: MachineCreate) -> Machine:
        db_machine = Machine(**machine.dict())
        self.db.add(db_machine)
        self.db.commit()
        self.db.refresh(db_machine)
        return db_machine
    
    def update(self, machine_id: int, machine_update: dict) -> Optional[Machine]:
        machine = self.get(machine_id)
        if not machine:
            return None
        
        for field, value in machine_update.items():
            if value is not None:
                setattr(machine, field, value)
        
        self.db.commit()
        self.db.refresh(machine)
        return machine
    
    def delete(self, machine_id: int) -> Optional[Machine]:
        machine = self.get(machine_id)
        if machine:
            self.db.delete(machine)
            self.db.commit()
        return machine


class BookingRepository(BaseRepository):
    """Репозиторий для работы с бронированиями"""
    
    def get(self, booking_id: int) -> Optional[Booking]:
        return self.db.query(Booking).filter(Booking.id == booking_id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> List[Booking]:
        """
        Получение списка бронирований с фильтрацией и сортировкой.
        """
        query = self.db.query(Booking)
        
        # Фильтр по пользователю
        if user_id:
            query = query.filter(Booking.user_id == user_id)
        
        # Фильтр по машине
        if machine_id:
            query = query.filter(Booking.machine_id == machine_id)
        
        # Фильтр по статусу
        if status:
            query = query.filter(Booking.status == status)
        
        # Фильтр по дате начала
        if start_date:
            query = query.filter(Booking.start_time >= start_date)
        
        # Фильтр по дате окончания
        if end_date:
            query = query.filter(Booking.end_time <= end_date)
        
        # Сортировка
        if sort_by:
            sort_column = getattr(Booking, sort_by, None)
            if sort_column:
                if sort_order.lower() == "desc":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        
        return query.offset(skip).limit(limit).all()
    
    def count(
        self,
        user_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """Подсчет общего количества с учетом фильтров"""
        query = self.db.query(Booking)
        
        if user_id:
            query = query.filter(Booking.user_id == user_id)
        if machine_id:
            query = query.filter(Booking.machine_id == machine_id)
        if status:
            query = query.filter(Booking.status == status)
        
        return query.count()
    
    def get_by_user(self, user_id: Optional[int] = None, user_name: Optional[str] = None) -> List[Booking]:
        if user_id:
            return self.db.query(Booking).filter(Booking.user_id == user_id).all()
        if user_name:
            return self.db.query(Booking).filter(Booking.user_name == user_name).all()
        return []
    
    def create(self, booking: BookingCreate, user_id: Optional[int] = None, 
               user_name: Optional[str] = None) -> Optional[Booking]:
        # Проверка конфликтов
        if not self._check_availability(booking.machine_id, booking.start_time, booking.end_time):
            return None
        
        db_booking = Booking(
            **booking.dict(),
            user_id=user_id,
            user_name=user_name
        )
        self.db.add(db_booking)
        self.db.commit()
        self.db.refresh(db_booking)
        return db_booking
    
    def _check_availability(self, machine_id: int, start_time: datetime, 
                           end_time: datetime) -> bool:
        """Проверяет, нет ли конфликтов с существующими бронированиями"""
        conflicting = self.db.query(Booking).filter(
            Booking.machine_id == machine_id,
            Booking.status == "active",
            or_(
                and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
            )
        ).first()
        return conflicting is None
    
    def update(self, booking_id: int, booking_update: dict) -> Optional[Booking]:
        booking = self.get(booking_id)
        if not booking:
            return None
        
        for field, value in booking_update.items():
            if value is not None:
                setattr(booking, field, value)
        
        self.db.commit()
        self.db.refresh(booking)
        return booking
    
    def cancel(self, booking_id: int) -> Optional[Booking]:
        booking = self.get(booking_id)
        if booking:
            booking.status = "cancelled"
            self.db.commit()
            self.db.refresh(booking)
        return booking
    
    def delete(self, booking_id: int) -> Optional[Booking]:
        booking = self.get(booking_id)
        if booking:
            self.db.delete(booking)
            self.db.commit()
        return booking
