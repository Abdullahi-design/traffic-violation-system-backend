from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "officer"
    phone: str | None = None
    badge_number: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    phone: str | None = None
    badge_number: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    phone: str | None = None
    badge_number: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int
