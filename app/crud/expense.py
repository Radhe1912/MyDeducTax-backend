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
        hashes = [e["txn_hash"] for e in expenses]

        existing = await db.execute(
            select(Expense.txn_hash).where(Expense.txn_hash.in_(hashes))
        )

        existing_hashes = set(existing.scalars().all())

        new_expenses = [e for e in expenses if e["txn_hash"] not in existing_hashes]

        objects = [
            Expense(
                user_id=user_id,
                description=e.get("description"),
                amount=e.get("amount"),
                transaction_date=e.get("transaction_date"),
                category=e.get("category"),
                sub_category=e.get("sub_category"),
                raw_data=e.get("raw_data"),
                source=e.get("source", "csv"),
                txn_hash=e.get("txn_hash") 
            )
            for e in new_expenses
        ]

        db.add_all(objects)
        await db.commit()

        return objects

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