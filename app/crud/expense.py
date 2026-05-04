from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from typing import List
from app.models.expense import Expense
from app.crud.base import CRUDBase

class CRUDExpense(CRUDBase[Expense]):

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id,
        skip: int = 0,
        limit: int = 100
    ):
        result = await db.execute(
            select(Expense)
            .where(Expense.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def bulk_insert_transactions(self, db, user_id, expenses):
        inserted = 0

        for e in expenses:
            exists = await db.execute(
                select(Expense).where(
                    Expense.user_id == user_id,
                    Expense.txn_hash == e["txn_hash"]
                )
            )

            if exists.scalar():
                continue

            obj = Expense(
                user_id=user_id,
                description=e["description"],
                amount=e["amount"],
                category=e.get("category"),
                sub_category=e.get("sub_category"),
                txn_hash=e["txn_hash"],
                transaction_date=e["transaction_date"]
            )

            db.add(obj)
            inserted += 1

        await db.commit()
        return inserted

    async def get_for_deduction(
        self,
        db: AsyncSession,
        user_id
    ):
        """
        Fetch only relevant fields for deduction engine
        """

        result = await db.execute(
            select(
                Expense.id,
                Expense.amount,
                Expense.category,
                Expense.sub_category
            ).where(Expense.user_id == user_id)
        )

        rows = result.all()

        return [
            {
                "id": r.id,
                "amount": float(r.amount),
                "category": r.category,
                "sub_category": r.sub_category
            }
            for r in rows
        ]


expense_crud = CRUDExpense(Expense)