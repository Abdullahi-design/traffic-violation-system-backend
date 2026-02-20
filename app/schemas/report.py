from pydantic import BaseModel
from decimal import Decimal
from app.schemas.violation import ViolationResponse
from app.schemas.payment import PaymentResponse


class SummaryReport(BaseModel):
    total_violations: int
    total_fines: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    collection_rate: float
    violations_today: int
    violations_this_week: int
    violations_this_month: int


class TrendItem(BaseModel):
    period: str
    count: int


class ViolationByType(BaseModel):
    type_name: str
    count: int
    total_fines: Decimal


class PaymentSummary(BaseModel):
    total_collected: Decimal
    total_outstanding: Decimal
    collection_rate: float
    payments_count: int


class PaymentByMethod(BaseModel):
    method: str
    count: int
    total: Decimal


class OfficerPerformance(BaseModel):
    officer_id: int
    officer_name: str
    badge_number: str | None = None
    violations_count: int
    total_fines: Decimal


class PeakHourItem(BaseModel):
    hour: int
    count: int


class RepeatOffender(BaseModel):
    vehicle_number: str
    violations_count: int
    total_fines: Decimal
    total_paid: Decimal


class DashboardAdmin(BaseModel):
    total_violations: int
    total_fines: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    collection_rate: float
    violations_today: int
    violations_this_week: int
    violations_this_month: int
    recent_violations: list[ViolationResponse] = []
    violations_by_type: list[ViolationByType] = []
    recent_payments: list[PaymentResponse] = []


class DashboardOfficer(BaseModel):
    violations_today: int
    violations_this_week: int
    violations_this_month: int
    recent_violations: list[ViolationResponse] = []
