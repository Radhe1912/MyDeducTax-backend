from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class SectionDeduction(BaseModel):
    section: str
    amount: float
    count: int
    limit: Optional[float] = None
    remaining: Optional[float] = None

class Recommendation(BaseModel):
    section_code: str
    message: str
    potential_savings: float

class DeductionSummary(BaseModel):
    sections: List[SectionDeduction]
    recommendations: List[Recommendation]
    total_deduction: float