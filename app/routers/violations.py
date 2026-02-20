import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.user import User
from app.models.violation import Violation
from app.models.violation_type import ViolationType
from app.schemas.violation import ViolationCreate, ViolationUpdate, ViolationResponse, ViolationListResponse
from app.dependencies import get_current_user, require_admin
from app.utils.pagination import paginate
from app.utils.filters import parse_date
from app.config import get_settings

router = APIRouter(prefix="/api/violations", tags=["Violations"])


@router.get("", response_model=ViolationListResponse)
async def list_violations(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    sort_by: str = Query("date_time", pattern="^(date_time|fine_amount|vehicle_number|payment_status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    search: str | None = None,
    violation_type_id: int | None = None,
    payment_status: str | None = None,
    officer_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Violation).options(
        joinedload(Violation.violation_type),
        joinedload(Violation.officer),
        joinedload(Violation.payments),
    )

    # Officers can only see their own violations
    if current_user.role != "admin":
        query = query.where(Violation.officer_id == current_user.id)
    elif officer_id:
        query = query.where(Violation.officer_id == officer_id)

    if search:
        query = query.where(
            or_(
                Violation.vehicle_number.ilike(f"%{search}%"),
                Violation.location.ilike(f"%{search}%"),
                Violation.description.ilike(f"%{search}%"),
            )
        )
    if violation_type_id:
        query = query.where(Violation.violation_type_id == violation_type_id)
    if payment_status:
        query = query.where(Violation.payment_status == payment_status)

    from_date = parse_date(date_from)
    to_date = parse_date(date_to)
    if from_date:
        query = query.where(Violation.date_time >= from_date)
    if to_date:
        query = query.where(Violation.date_time <= to_date)

    sort_column = getattr(Violation, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    result = await paginate(db, query, page, per_page)
    return ViolationListResponse(**result)


@router.post("", response_model=ViolationResponse, status_code=status.HTTP_201_CREATED)
async def create_violation(
    data: ViolationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify violation type exists
    vt_result = await db.execute(select(ViolationType).where(ViolationType.id == data.violation_type_id))
    if not vt_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation type not found")

    violation = Violation(
        vehicle_number=data.vehicle_number,
        violation_type_id=data.violation_type_id,
        officer_id=current_user.id,
        date_time=data.date_time,
        location=data.location,
        fine_amount=data.fine_amount,
        description=data.description,
    )
    db.add(violation)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Violation)
        .options(joinedload(Violation.violation_type), joinedload(Violation.officer))
        .where(Violation.id == violation.id)
    )
    return result.unique().scalar_one()


@router.get("/{violation_id}", response_model=ViolationResponse)
async def get_violation(
    violation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Violation)
        .options(
            joinedload(Violation.violation_type),
            joinedload(Violation.officer),
            joinedload(Violation.payments),
        )
        .where(Violation.id == violation_id)
    )
    violation = result.unique().scalar_one_or_none()

    if not violation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    if current_user.role != "admin" and violation.officer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return violation


@router.put("/{violation_id}", response_model=ViolationResponse)
async def update_violation(
    violation_id: int,
    data: ViolationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Violation)
        .options(joinedload(Violation.violation_type), joinedload(Violation.officer))
        .where(Violation.id == violation_id)
    )
    violation = result.unique().scalar_one_or_none()

    if not violation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    if current_user.role != "admin" and violation.officer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if data.vehicle_number is not None:
        violation.vehicle_number = data.vehicle_number
    if data.violation_type_id is not None:
        violation.violation_type_id = data.violation_type_id
    if data.date_time is not None:
        violation.date_time = data.date_time
    if data.location is not None:
        violation.location = data.location
    if data.fine_amount is not None:
        violation.fine_amount = data.fine_amount
    if data.description is not None:
        violation.description = data.description

    await db.flush()
    await db.refresh(violation)
    return violation


@router.delete("/{violation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_violation(
    violation_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    violation = result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    await db.delete(violation)
    await db.flush()


@router.post("/{violation_id}/upload", response_model=ViolationResponse)
async def upload_evidence(
    violation_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Violation)
        .options(joinedload(Violation.violation_type), joinedload(Violation.officer))
        .where(Violation.id == violation_id)
    )
    violation = result.unique().scalar_one_or_none()

    if not violation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    if current_user.role != "admin" and violation.officer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    settings = get_settings()
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(violation_id))
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    violation.evidence_path = f"/uploads/{violation_id}/{filename}"
    await db.flush()
    await db.refresh(violation)
    return violation
