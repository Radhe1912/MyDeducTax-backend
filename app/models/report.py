from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base_class import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)

    income = Column(Float, nullable=False)
    total_deduction = Column(Float, nullable=False)
    tax_payable = Column(Float, nullable=False)

    breakdown = Column(Text, nullable=False)  # JSON string

    created_at = Column(DateTime, default=datetime.utcnow)