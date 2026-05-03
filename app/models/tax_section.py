from sqlalchemy import Column, String, Numeric, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.db.base_class import Base

class TaxSection(Base):
    __tablename__ = "tax_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_code = Column(String, nullable=False, index=True)  # 80C, 80D, HRA
    name = Column(String, nullable=False)
    max_limit = Column(Numeric, nullable=True)
    rule_type = Column(String, nullable=False)
    rules_metadata = Column(JSON, nullable=True)
    rules = Column(JSONB, nullable=True)
    """
    Example:
    {
      "allowed_categories": ["insurance", "investment"],
      "percentage": 100,
      "conditions": {
          "age": "<60"
      }
    }
    """
    created_at = Column(DateTime, default=datetime.utcnow)