from sqlalchemy import Column, Integer, Float, ForeignKey
from app.db.base import Base

class DeductionLog(Base):
    __tablename__ = "deduction_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    section_id = Column(Integer, ForeignKey("tax_sections.id"))
    amount_claimed = Column(Float)
