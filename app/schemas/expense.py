from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID

class ExpenseBase(BaseModel):
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    transaction_date: Optional[datetime] = None

class ExpenseCreate(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    category: Optional[str] = None
    sub_category: Optional[str] = None


class ExpenseOut(BaseModel):
    id: UUID
    description: str
    amount: float
    category: Optional[str]
    sub_category: Optional[str]

    class Config:
        from_attributes = True

class ExpenseBulkCreate(BaseModel):
    expenses: List[ExpenseBase]

class ExpenseResponse(BaseModel):
    id: UUID
    description: Optional[str]
    amount: float
    category: Optional[str]
    sub_category: Optional[str]
    transaction_date: Optional[datetime]

    class Config:
        from_attributes = True