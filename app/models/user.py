from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum("admin", "officer", name="user_role"), nullable=False, default="officer")
    phone = Column(String(20), nullable=True)
    badge_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    violations = relationship("Violation", back_populates="officer", foreign_keys="Violation.officer_id")
    payments_received = relationship("Payment", back_populates="receiver", foreign_keys="Payment.received_by")
    notifications = relationship("Notification", back_populates="user")
