from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, extract
from app.database import get_db
from app.models.user import User
from app.models.violation import Violation
from app.models.violation_type import ViolationType
from app.models.payment import Payment
from app.schemas.report import (
    SummaryReport, TrendItem, ViolationByType, PaymentSummary,
    PaymentByMethod, OfficerPerformance, PeakHourItem, RepeatOffender,
)
from app.dependencies import require_admin
from app.services.report_service import generate_pdf_report, generate_excel_report
from app.utils.filters import parse_date
import io

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def apply_date_filters(query, date_from: str | None, date_to: str | None, date_col):
    from_date = parse_date(date_from)
    to_date = parse_date(date_to)
    if from_date:
        query = query.where(date_col >= from_date)
    if to_date:
        query = query.where(date_col <= to_date)
    return query


@router.get("/summary", response_model=SummaryReport)
async def get_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Total violations and fines
    stats_query = select(
        func.count(Violation.id),
        func.coalesce(func.sum(Violation.fine_amount), Decimal("0")),
    )
    stats_query = apply_date_filters(stats_query, date_from, date_to, Violation.date_time)
    stats = await db.execute(stats_query)
    total_violations, total_fines = stats.one()

    # Total collected
    payment_query = select(func.coalesce(func.sum(Payment.amount), Decimal("0")))
    if date_from or date_to:
        payment_query = apply_date_filters(payment_query, date_from, date_to, Payment.payment_date)
    collected_result = await db.execute(payment_query)
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

    return SummaryReport(
        total_violations=total_violations,
        total_fines=total_fines,
        total_collected=total_collected,
        total_outstanding=total_outstanding,
        collection_rate=round(collection_rate, 1),
        violations_today=violations_today,
        violations_this_week=violations_this_week,
        violations_this_month=violations_this_month,
    )


@router.get("/violations/trends", response_model=list[TrendItem])
async def violation_trends(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if period == "daily":
        date_expr = func.date(Violation.date_time)
    elif period == "weekly":
        date_expr = func.yearweek(Violation.date_time)
    else:
        date_expr = func.date_format(Violation.date_time, "%Y-%m")

    query = (
        select(date_expr.label("period"), func.count(Violation.id).label("count"))
        .group_by("period")
        .order_by("period")
    )
    query = apply_date_filters(query, date_from, date_to, Violation.date_time)

    result = await db.execute(query)
    return [TrendItem(period=str(row.period), count=row.count) for row in result.all()]


@router.get("/violations/by-type", response_model=list[ViolationByType])
async def violations_by_type(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = (
        select(
            ViolationType.name,
            func.count(Violation.id).label("count"),
            func.coalesce(func.sum(Violation.fine_amount), Decimal("0")).label("total_fines"),
        )
        .join(ViolationType, Violation.violation_type_id == ViolationType.id)
        .group_by(ViolationType.name)
        .order_by(func.count(Violation.id).desc())
    )
    query = apply_date_filters(query, date_from, date_to, Violation.date_time)

    result = await db.execute(query)
    return [
        ViolationByType(type_name=row.name, count=row.count, total_fines=row.total_fines)
        for row in result.all()
    ]


@router.get("/payments/summary", response_model=PaymentSummary)
async def payments_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    fines_result = await db.execute(
        select(func.coalesce(func.sum(Violation.fine_amount), Decimal("0")))
    )
    total_fines = fines_result.scalar() or Decimal("0")

    pay_query = select(
        func.coalesce(func.sum(Payment.amount), Decimal("0")).label("total"),
        func.count(Payment.id).label("count"),
    )
    pay_query = apply_date_filters(pay_query, date_from, date_to, Payment.payment_date)
    pay_result = await db.execute(pay_query)
    row = pay_result.one()

    total_collected = row.total or Decimal("0")
    total_outstanding = total_fines - total_collected
    rate = float(total_collected / total_fines * 100) if total_fines > 0 else 0.0

    return PaymentSummary(
        total_collected=total_collected,
        total_outstanding=total_outstanding,
        collection_rate=round(rate, 1),
        payments_count=row.count,
    )


@router.get("/payments/by-method", response_model=list[PaymentByMethod])
async def payments_by_method(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = (
        select(
            Payment.payment_method,
            func.count(Payment.id).label("count"),
            func.coalesce(func.sum(Payment.amount), Decimal("0")).label("total"),
        )
        .group_by(Payment.payment_method)
        .order_by(func.sum(Payment.amount).desc())
    )
    query = apply_date_filters(query, date_from, date_to, Payment.payment_date)

    result = await db.execute(query)
    return [
        PaymentByMethod(method=row.payment_method, count=row.count, total=row.total)
        for row in result.all()
    ]


@router.get("/officers/performance", response_model=list[OfficerPerformance])
async def officers_performance(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = (
        select(
            User.id,
            User.full_name,
            User.badge_number,
            func.count(Violation.id).label("violations_count"),
            func.coalesce(func.sum(Violation.fine_amount), Decimal("0")).label("total_fines"),
        )
        .join(Violation, User.id == Violation.officer_id)
        .group_by(User.id, User.full_name, User.badge_number)
        .order_by(func.count(Violation.id).desc())
    )
    query = apply_date_filters(query, date_from, date_to, Violation.date_time)

    result = await db.execute(query)
    return [
        OfficerPerformance(
            officer_id=row.id,
            officer_name=row.full_name,
            badge_number=row.badge_number,
            violations_count=row.violations_count,
            total_fines=row.total_fines,
        )
        for row in result.all()
    ]


@router.get("/peak-hours", response_model=list[PeakHourItem])
async def peak_hours(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = (
        select(
            extract("hour", Violation.date_time).label("hour"),
            func.count(Violation.id).label("count"),
        )
        .group_by("hour")
        .order_by("hour")
    )
    query = apply_date_filters(query, date_from, date_to, Violation.date_time)

    result = await db.execute(query)
    return [PeakHourItem(hour=int(row.hour), count=row.count) for row in result.all()]


@router.get("/repeat-offenders", response_model=list[RepeatOffender])
async def repeat_offenders(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    # Subquery for total paid per violation
    paid_subq = (
        select(
            Payment.violation_id,
            func.coalesce(func.sum(Payment.amount), Decimal("0")).label("paid"),
        )
        .group_by(Payment.violation_id)
        .subquery()
    )

    query = (
        select(
            Violation.vehicle_number,
            func.count(Violation.id).label("violations_count"),
            func.coalesce(func.sum(Violation.fine_amount), Decimal("0")).label("total_fines"),
            func.coalesce(func.sum(paid_subq.c.paid), Decimal("0")).label("total_paid"),
        )
        .outerjoin(paid_subq, Violation.id == paid_subq.c.violation_id)
        .group_by(Violation.vehicle_number)
        .having(func.count(Violation.id) >= 2)
        .order_by(func.count(Violation.id).desc())
    )
    query = apply_date_filters(query, date_from, date_to, Violation.date_time)

    result = await db.execute(query)
    return [
        RepeatOffender(
            vehicle_number=row.vehicle_number,
            violations_count=row.violations_count,
            total_fines=row.total_fines,
            total_paid=row.total_paid,
        )
        for row in result.all()
    ]


@router.get("/export/pdf")
async def export_pdf(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    # Gather violations data
    query = (
        select(Violation)
        .join(ViolationType, Violation.violation_type_id == ViolationType.id)
        .join(User, Violation.officer_id == User.id)
        .add_columns(ViolationType.name.label("type_name"), User.full_name.label("officer_name"))
        .order_by(Violation.date_time.desc())
    )
    query = apply_date_filters(query, date_from, date_to, Violation.date_time)

    result = await db.execute(query)
    rows_data = result.all()

    headers = ["ID", "Vehicle", "Type", "Officer", "Date", "Amount", "Status"]
    rows = []
    for row in rows_data:
        v = row[0]
        rows.append([
            v.id, v.vehicle_number, row.type_name, row.officer_name,
            v.date_time.strftime("%Y-%m-%d %H:%M"), f"₦{v.fine_amount:,.2f}", v.payment_status
        ])

    pdf_bytes = generate_pdf_report("Traffic Violations Report", headers, rows)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=violations_report.pdf"},
    )


@router.get("/export/excel")
async def export_excel(
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = (
        select(Violation)
        .join(ViolationType, Violation.violation_type_id == ViolationType.id)
        .join(User, Violation.officer_id == User.id)
        .add_columns(ViolationType.name.label("type_name"), User.full_name.label("officer_name"))
        .order_by(Violation.date_time.desc())
    )
    query = apply_date_filters(query, date_from, date_to, Violation.date_time)

    result = await db.execute(query)
    rows_data = result.all()

    headers = ["ID", "Vehicle", "Type", "Officer", "Date", "Amount", "Status"]
    rows = []
    for row in rows_data:
        v = row[0]
        rows.append([
            v.id, v.vehicle_number, row.type_name, row.officer_name,
            v.date_time.strftime("%Y-%m-%d %H:%M"), float(v.fine_amount), v.payment_status
        ])

    excel_bytes = generate_excel_report("Violations Report", headers, rows)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=violations_report.xlsx"},
    )
