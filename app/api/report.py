from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.api.deps import get_db, get_current_user
from app.models.report import Report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/history")
async def get_history(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(
        select(Report)
        .where(Report.user_id == user["user_id"])
        .order_by(Report.created_at.desc())
    )

    reports = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "income": r.income,
            "total_deduction": r.total_deduction,
            "tax_payable": r.tax_payable,
            "created_at": r.created_at,
            "breakdown": json.loads(r.breakdown) if r.breakdown else {}
        }
        for r in reports
    ]