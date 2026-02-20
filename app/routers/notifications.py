from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationListResponse, UnreadCountResponse
from app.dependencies import get_current_user
from app.utils.pagination import paginate

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    count = result.scalar() or 0
    return UnreadCountResponse(count=count)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )

    result = await paginate(db, query, page, per_page)
    return NotificationListResponse(**result)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.is_read = True
    await db.flush()
    await db.refresh(notification)
    return notification


@router.patch("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.flush()
    return {"message": "All notifications marked as read"}
