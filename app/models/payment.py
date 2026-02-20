from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Enum, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(
        Enum("cash", "bank_transfer", "online", "pos", name="payment_method_enum"),
        nullable=False,
    )
    payment_date = Column(DateTime, nullable=False)
    receipt_number = Column(String(100), nullable=True)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    violation = relationship("Violation", back_populates="payments")
    receiver = relationship("User", back_populates="payments_received", foreign_keys=[received_by])

    __table_args__ = (
        Index("idx_violation", "violation_id"),
        Index("idx_payment_date", "payment_date"),
    )
