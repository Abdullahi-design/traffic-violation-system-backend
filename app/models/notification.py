from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(
        Enum("info", "warning", "success", "error", name="notification_type_enum"),
        default="info",
    )
    is_read = Column(Boolean, default=False)
    related_id = Column(Integer, nullable=True)
    related_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_user_read", "user_id", "is_read"),
    )
