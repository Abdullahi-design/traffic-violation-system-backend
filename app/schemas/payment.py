from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class PaymentCreate(BaseModel):
    violation_id: int
    amount: Decimal
    payment_method: str
    payment_date: datetime
    receipt_number: str | None = None
    notes: str | None = None


class ViolationInPayment(BaseModel):
    id: int
    vehicle_number: str
    fine_amount: Decimal
    payment_status: str

    model_config = {"from_attributes": True}


class ReceiverInPayment(BaseModel):
    id: int
    full_name: str

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: int
    violation_id: int
    amount: Decimal
    payment_method: str
    payment_date: datetime
    receipt_number: str | None = None
    received_by: int
    notes: str | None = None
    created_at: datetime | None = None
    violation: ViolationInPayment | None = None
    receiver: ReceiverInPayment | None = None

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    per_page: int
    pages: int
