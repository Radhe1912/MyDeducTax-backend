from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.expense import ExpenseCreate
from app.schemas.deduction import DeductionSummary

class TaxCalculationInput(BaseModel):
    income: float = Field(..., ge=0)
    expenses: List[ExpenseCreate]
    hra_received: Optional[float] = Field(0, ge=0)
    is_metro: Optional[bool] = True
    is_senior_self: Optional[bool] = False
    is_senior_parents: Optional[bool] = False

class TaxResult(BaseModel):
    income: float
    taxable_income: float
    total_deduction: float
    tax_payable: float
    regime: str

class TaxCalculationResponse(BaseModel):
    old_regime: TaxResult
    new_regime: TaxResult
    recommended_regime: str
    savings: float
    deductions: DeductionSummary