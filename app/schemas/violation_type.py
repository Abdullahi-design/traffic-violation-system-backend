from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class ViolationTypeCreate(BaseModel):
    name: str
    default_fine: Decimal
    description: str | None = None


class ViolationTypeUpdate(BaseModel):
    name: str | None = None
    default_fine: Decimal | None = None
    description: str | None = None


class ViolationTypeStatusUpdate(BaseModel):
    is_active: bool


class ViolationTypeResponse(BaseModel):
    id: int
    name: str
    default_fine: Decimal
    description: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
