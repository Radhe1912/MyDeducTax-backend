from pydantic import BaseModel

class DeductionBreakdown(BaseModel):
    section: str
    eligible_amount: float
    claimed_amount: float
