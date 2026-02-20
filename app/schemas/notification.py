from pydantic import BaseModel
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    related_id: int | None = None
    related_type: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class UnreadCountResponse(BaseModel):
    count: int
