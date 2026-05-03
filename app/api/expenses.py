from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseOut
from sqlalchemy import select, delete
import uuid

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.post("/", response_model=ExpenseOut)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    expense = Expense(
        id=uuid.uuid4(),
        user_id=user["user_id"],
        description=data.description,
        amount=data.amount,
        category=data.category,
        sub_category=data.sub_category
    )

    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    return expense


@router.get("/", response_model=List[ExpenseOut])
async def get_expenses(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(
        select(Expense).where(Expense.user_id == user["user_id"])
    )
    return result.scalars().all()


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    await db.execute(
        delete(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == user["user_id"]
        )
    )
    await db.commit()

    return {"message": "Expense deleted"}