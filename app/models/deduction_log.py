from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.db.base_class import Base

class DeductionLog(Base):
    __tablename__ = "deduction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    section_code = Column(String, nullable=False)
    total_claimed = Column(Numeric, nullable=False)
    total_allowed = Column(Numeric, nullable=False)
    remaining_limit = Column(Numeric, nullable=True)
    breakdown = Column(JSON, nullable=True)
    """
    Example:
    [
      {
        "expense_id": "...",
        "amount": 20000,
        "applied": 20000,
        "reason": "Eligible under 80D"
      }
    ]
    """
    rule_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)