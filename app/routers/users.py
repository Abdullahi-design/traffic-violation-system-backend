from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserStatusUpdate, UserResponse, UserListResponse
from app.services.auth_service import hash_password
from app.dependencies import require_admin
from app.utils.pagination import paginate

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    role: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        query = query.where(
            (User.full_name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    query = query.order_by(User.created_at.desc())

    result = await paginate(db, query, page, per_page)
    return UserListResponse(**result)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        phone=data.phone,
        badge_number=data.badge_number,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.email is not None:
        existing = await db.execute(select(User).where(User.email == data.email, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        user.email = data.email
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.phone is not None:
        user.phone = data.phone
    if data.badge_number is not None:
        user.badge_number = data.badge_number

    await db.flush()
    await db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = data.is_active
    await db.flush()
    await db.refresh(user)
    return user
