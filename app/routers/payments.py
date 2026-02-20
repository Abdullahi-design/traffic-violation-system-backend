from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.user import User
from app.models.violation import Violation
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentListResponse
from app.dependencies import get_current_user
from app.services.notification_service import notify_admins
from app.utils.pagination import paginate
from app.utils.filters import parse_date

router = APIRouter(prefix="/api/payments", tags=["Payments"])


async def update_violation_payment_status(db: AsyncSession, violation_id: int):
    result = await db.execute(select(Violation).where(Violation.id == violation_id))
    violation = result.scalar_one_or_none()
    if not violation:
        return

    total_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), Decimal("0")))
        .where(Payment.violation_id == violation_id)
    )
    total_paid = total_result.scalar() or Decimal("0")

    if total_paid >= violation.fine_amount:
        violation.payment_status = "paid"
    elif total_paid > 0:
        violation.payment_status = "partial"
    else:
        violation.payment_status = "unpaid"

    await db.flush()


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    violation_id: int | None = None,
    payment_method: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Payment).options(
        joinedload(Payment.violation),
        joinedload(Payment.receiver),
    )

    if current_user.role != "admin":
        query = query.where(Payment.received_by == current_user.id)

    if violation_id:
        query = query.where(Payment.violation_id == violation_id)
    if payment_method:
        query = query.where(Payment.payment_method == payment_method)

    from_date = parse_date(date_from)
    to_date = parse_date(date_to)
    if from_date:
        query = query.where(Payment.payment_date >= from_date)
    if to_date:
        query = query.where(Payment.payment_date <= to_date)

    query = query.order_by(Payment.created_at.desc())

    result = await paginate(db, query, page, per_page)
    return PaymentListResponse(**result)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify violation exists
    v_result = await db.execute(select(Violation).where(Violation.id == data.violation_id))
    violation = v_result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    payment = Payment(
        violation_id=data.violation_id,
        amount=data.amount,
        payment_method=data.payment_method,
        payment_date=data.payment_date,
        receipt_number=data.receipt_number,
        received_by=current_user.id,
        notes=data.notes,
    )
    db.add(payment)
    await db.flush()

    # Update violation payment status
    await update_violation_payment_status(db, data.violation_id)

    # Notify admins
    await notify_admins(
        db,
        title="Payment Received",
        message=f"Payment of ₦{data.amount:,.2f} received for violation #{data.violation_id} (Vehicle: {violation.vehicle_number})",
        type="success",
        related_id=payment.id,
        related_type="payment",
    )

    # Reload with relationships
    result = await db.execute(
        select(Payment)
        .options(joinedload(Payment.violation), joinedload(Payment.receiver))
        .where(Payment.id == payment.id)
    )
    return result.unique().scalar_one()


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment)
        .options(joinedload(Payment.violation), joinedload(Payment.receiver))
        .where(Payment.id == payment_id)
    )
    payment = result.unique().scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if current_user.role != "admin" and payment.received_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return payment
