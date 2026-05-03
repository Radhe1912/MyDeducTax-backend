from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base

class TaxSection(Base):
    __tablename__ = "tax_sections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., 80C
    description = Column(String)
    max_limit = Column(Float)
