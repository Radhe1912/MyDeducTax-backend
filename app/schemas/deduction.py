from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class DeductionItem(BaseModel):
    expense_id: Optional[UUID]
    amount: float
    applied: float
    reason: str

class SectionDeduction(BaseModel):
    section_code: str
    total_claimed: float
    total_allowed: float
    remaining_limit: Optional[float]

    breakdown: List[DeductionItem]

class Recommendation(BaseModel):
    section_code: str
    message: str
    potential_savings: float

class DeductionSummary(BaseModel):
    sections: List[SectionDeduction]
    recommendations: List[Recommendation]
    total_deduction: float