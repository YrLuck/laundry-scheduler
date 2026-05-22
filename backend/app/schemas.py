from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Permission schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = []

class Role(RoleBase):
    id: int
    created_at: datetime
    permissions: List[Permission] = []

    class Config:
        from_attributes = True

class RoleWithPermissions(Role):
    pass

# Machine schemas
class MachineBase(BaseModel):
    name: str
    type: str
    status: Optional[str] = "available"

class MachineCreate(MachineBase):
    pass

class Machine(MachineBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Booking schemas
class BookingBase(BaseModel):
    machine_id: int
    start_time: datetime
    end_time: datetime

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    machine_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class Booking(BookingBase):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class BookingWithMachine(Booking):
    machine: Machine

# User schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role_id: Optional[int] = None

class UserUpdate(UserBase):
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    role_id: Optional[int] = None
    role: Optional[Role] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None