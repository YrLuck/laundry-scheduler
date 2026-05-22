from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Ассоциативная таблица many-to-many: одна роль — много разрешений, одно разрешение — много ролей
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)

class Permission(Base):
    """Модель разрешений (permissions)"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # например: "machines:create"
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class Role(Base):
    """Модель ролей (roles)"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # "guest", "user", "admin"
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", back_populates="role")

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)    # "washer" | "dryer"
    status = Column(String, default="available")  # "available" | "in_use" | "maintenance"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("Booking", back_populates="machine")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_name = Column(String, index=True)  # денормализованное имя для быстрого отображения без JOIN
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String, default="active")  # "active" | "completed" | "cancelled"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    machine = relationship("Machine", back_populates="bookings")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)  # Связь с ролью
    role = relationship("Role", back_populates="users")
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())