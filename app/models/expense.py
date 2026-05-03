from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.db.base_class import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    description = Column(String, nullable=True)
    amount = Column(Numeric, nullable=False)
    txn_hash = Column(String, nullable=False, index=True)
    transaction_date = Column(DateTime, nullable=True)
    source = Column(String, nullable=False, default="manual")
    category = Column(String, nullable=True)  
    sub_category = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)