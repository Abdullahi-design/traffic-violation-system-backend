from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, func
from sqlalchemy.orm import relationship
from app.database import Base


class ViolationType(Base):
    __tablename__ = "violation_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    default_fine = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    violations = relationship("Violation", back_populates="violation_type")
