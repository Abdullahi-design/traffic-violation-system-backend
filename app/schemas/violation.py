from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class ViolationCreate(BaseModel):
    vehicle_number: str
    violation_type_id: int
    date_time: datetime
    location: str | None = None
    fine_amount: Decimal
    description: str | None = None


class ViolationUpdate(BaseModel):
    vehicle_number: str | None = None
    violation_type_id: int | None = None
    date_time: datetime | None = None
    location: str | None = None
    fine_amount: Decimal | None = None
    description: str | None = None


class PaymentInViolation(BaseModel):
    id: int
    amount: Decimal
    payment_method: str
    payment_date: datetime
    receipt_number: str | None = None
    received_by: int
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ViolationTypeInViolation(BaseModel):
    id: int
    name: str
    default_fine: Decimal

    model_config = {"from_attributes": True}


class OfficerInViolation(BaseModel):
    id: int
    full_name: str
    badge_number: str | None = None

    model_config = {"from_attributes": True}


class ViolationResponse(BaseModel):
    id: int
    vehicle_number: str
    violation_type_id: int
    officer_id: int
    date_time: datetime
    location: str | None = None
    fine_amount: Decimal
    description: str | None = None
    evidence_path: str | None = None
    payment_status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    violation_type: ViolationTypeInViolation | None = None
    officer: OfficerInViolation | None = None
    payments: list[PaymentInViolation] = []

    model_config = {"from_attributes": True}


class ViolationListResponse(BaseModel):
    items: list[ViolationResponse]
    total: int
    page: int
    per_page: int
    pages: int
