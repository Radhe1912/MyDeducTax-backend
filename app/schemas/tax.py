from pydantic import BaseModel
from typing import List, Optional
from app.schemas.expense import ExpenseCreate
from app.schemas.deduction import DeductionSummary

class TaxCalculationInput(BaseModel):
    income: float
    expenses: List[ExpenseCreate]
    hra_received: Optional[float] = 0
    is_metro: Optional[bool] = True
    is_senior_self: Optional[bool] = False
    is_senior_parents: Optional[bool] = False

class TaxResult(BaseModel):
    income: float
    taxable_income: float
    total_deduction: float
    tax_payable: float

class TaxCalculationResponse(BaseModel):
    tax: TaxResult
    deductions: DeductionSummary