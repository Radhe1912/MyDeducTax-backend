from pydantic import BaseModel
from typing import List

class TaxCalculationRequest(BaseModel):
    user_id: int
    income: float
    year: int

class TaxCalculationResponse(BaseModel):
    total_tax: float
    effective_rate: float
