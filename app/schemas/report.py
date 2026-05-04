from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ReportOut(BaseModel):
    id: str
    income: float
    total_deduction: float
    tax_payable: float
    created_at: datetime
    breakdown: Any

    class Config:
        from_attributes = True