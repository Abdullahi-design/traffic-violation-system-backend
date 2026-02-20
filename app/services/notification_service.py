from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import Notification
from app.models.user import User


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    type: str = "info",
    related_id: int | None = None,
    related_type: str | None = None,
):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        related_id=related_id,
        related_type=related_type,
    )
    db.add(notification)
    await db.flush()
    return notification


async def notify_admins(
    db: AsyncSession,
    title: str,
    message: str,
    type: str = "info",
    related_id: int | None = None,
    related_type: str | None = None,
):
    result = await db.execute(select(User).where(User.role == "admin", User.is_active == True))
    admins = result.scalars().all()
    for admin in admins:
        await create_notification(db, admin.id, title, message, type, related_id, related_type)
