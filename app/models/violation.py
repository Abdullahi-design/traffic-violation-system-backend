from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Enum, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.database import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_number = Column(String(20), nullable=False)
    violation_type_id = Column(Integer, ForeignKey("violation_types.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_time = Column(DateTime, nullable=False)
    location = Column(String(500), nullable=True)
    fine_amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    evidence_path = Column(String(500), nullable=True)
    payment_status = Column(
        Enum("unpaid", "partial", "paid", name="payment_status_enum"),
        default="unpaid",
    )
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    violation_type = relationship("ViolationType", back_populates="violations")
    officer = relationship("User", back_populates="violations", foreign_keys=[officer_id])
    payments = relationship("Payment", back_populates="violation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_vehicle_number", "vehicle_number"),
        Index("idx_date_time", "date_time"),
        Index("idx_payment_status", "payment_status"),
        Index("idx_violation_type", "violation_type_id"),
        Index("idx_officer", "officer_id"),
    )
