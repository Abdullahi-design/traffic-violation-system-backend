from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.violation_type import ViolationType
from app.schemas.violation_type import (
    ViolationTypeCreate,
    ViolationTypeUpdate,
    ViolationTypeStatusUpdate,
    ViolationTypeResponse,
)
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/violation-types", tags=["Violation Types"])


@router.get("", response_model=list[ViolationTypeResponse])
async def list_violation_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ViolationType)
    if current_user.role != "admin":
        query = query.where(ViolationType.is_active == True)
    query = query.order_by(ViolationType.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ViolationTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_violation_type(
    data: ViolationTypeCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    existing = await db.execute(select(ViolationType).where(ViolationType.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Violation type already exists")

    vtype = ViolationType(name=data.name, default_fine=data.default_fine, description=data.description)
    db.add(vtype)
    await db.flush()
    await db.refresh(vtype)
    return vtype


@router.put("/{type_id}", response_model=ViolationTypeResponse)
async def update_violation_type(
    type_id: int,
    data: ViolationTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(ViolationType).where(ViolationType.id == type_id))
    vtype = result.scalar_one_or_none()
    if not vtype:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation type not found")

    if data.name is not None:
        existing = await db.execute(
            select(ViolationType).where(ViolationType.name == data.name, ViolationType.id != type_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Name already in use")
        vtype.name = data.name
    if data.default_fine is not None:
        vtype.default_fine = data.default_fine
    if data.description is not None:
        vtype.description = data.description

    await db.flush()
    await db.refresh(vtype)
    return vtype


@router.patch("/{type_id}/status", response_model=ViolationTypeResponse)
async def update_violation_type_status(
    type_id: int,
    data: ViolationTypeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(ViolationType).where(ViolationType.id == type_id))
    vtype = result.scalar_one_or_none()
    if not vtype:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation type not found")

    vtype.is_active = data.is_active
    await db.flush()
    await db.refresh(vtype)
    return vtype
