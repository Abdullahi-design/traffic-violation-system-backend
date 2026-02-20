from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.user import User
from app.models.violation import Violation
from app.models.violation_type import ViolationType
from app.models.payment import Payment
from app.schemas.report import DashboardAdmin, DashboardOfficer, ViolationByType
from app.schemas.violation import ViolationResponse
from app.schemas.payment import PaymentResponse
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/admin", response_model=DashboardAdmin)
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Total violations and fines
    stats = await db.execute(
        select(
            func.count(Violation.id),
            func.coalesce(func.sum(Violation.fine_amount), Decimal("0")),
        )
    )
    total_violations, total_fines = stats.one()

    # Total collected
    collected_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), Decimal("0")))
    )
    total_collected = collected_result.scalar() or Decimal("0")
    total_outstanding = total_fines - total_collected
    collection_rate = float(total_collected / total_fines * 100) if total_fines > 0 else 0.0

    # Time-based counts
    today_result = await db.execute(
        select(func.count(Violation.id)).where(Violation.date_time >= today_start)
    )
    violations_today = today_result.scalar() or 0

    week_result = await db.execute(
        select(func.count(Violation.id)).where(Violation.date_time >= week_start)
    )
    violations_this_week = week_result.scalar() or 0

    month_result = await db.execute(
        select(func.count(Violation.id)).where(Violation.date_time >= month_start)
    )
    violations_this_month = month_result.scalar() or 0

    # Recent violations
    recent_result = await db.execute(
        select(Violation)
        .options(joinedload(Violation.violation_type), joinedload(Violation.officer), joinedload(Violation.payments))
        .order_by(Violation.date_time.desc())
        .limit(10)
    )
    recent_violations = recent_result.unique().scalars().all()

    # Violations by type
    by_type_result = await db.execute(
        select(
            ViolationType.name,
            func.count(Violation.id).label("count"),
            func.coalesce(func.sum(Violation.fine_amount), Decimal("0")).label("total_fines"),
        )
        .join(ViolationType, Violation.violation_type_id == ViolationType.id)
        .group_by(ViolationType.name)
        .order_by(func.count(Violation.id).desc())
    )
    violations_by_type = [
        ViolationByType(type_name=row.name, count=row.count, total_fines=row.total_fines)
        for row in by_type_result.all()
    ]

    # Recent payments
    recent_pay_result = await db.execute(
        select(Payment)
        .options(joinedload(Payment.violation), joinedload(Payment.receiver))
        .order_by(Payment.created_at.desc())
        .limit(10)
    )
    recent_payments = recent_pay_result.unique().scalars().all()

    return DashboardAdmin(
        total_violations=total_violations,
        total_fines=total_fines,
        total_collected=total_collected,
        total_outstanding=total_outstanding,
        collection_rate=round(collection_rate, 1),
        violations_today=violations_today,
        violations_this_week=violations_this_week,
        violations_this_month=violations_this_month,
        recent_violations=[ViolationResponse.model_validate(v) for v in recent_violations],
        violations_by_type=violations_by_type,
        recent_payments=[PaymentResponse.model_validate(p) for p in recent_payments],
    )


@router.get("/officer", response_model=DashboardOfficer)
async def officer_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    base_filter = Violation.officer_id == current_user.id

    today_result = await db.execute(
        select(func.count(Violation.id)).where(base_filter, Violation.date_time >= today_start)
    )
    violations_today = today_result.scalar() or 0

    week_result = await db.execute(
        select(func.count(Violation.id)).where(base_filter, Violation.date_time >= week_start)
    )
    violations_this_week = week_result.scalar() or 0

    month_result = await db.execute(
        select(func.count(Violation.id)).where(base_filter, Violation.date_time >= month_start)
    )
    violations_this_month = month_result.scalar() or 0

    recent_result = await db.execute(
        select(Violation)
        .options(joinedload(Violation.violation_type), joinedload(Violation.officer), joinedload(Violation.payments))
        .where(base_filter)
        .order_by(Violation.date_time.desc())
        .limit(10)
    )
    recent_violations = recent_result.unique().scalars().all()

    return DashboardOfficer(
        violations_today=violations_today,
        violations_this_week=violations_this_week,
        violations_this_month=violations_this_month,
        recent_violations=[ViolationResponse.model_validate(v) for v in recent_violations],
    )
