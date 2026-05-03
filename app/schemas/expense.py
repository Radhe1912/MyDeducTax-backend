from pydantic import BaseModel
from typing import Optional

class ExpenseBase(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
