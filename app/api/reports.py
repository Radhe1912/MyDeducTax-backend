from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.deduction_log import DeductionLog

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/history")
async def get_history(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(
        select(DeductionLog)
        .where(DeductionLog.user_id == user["user_id"])
        .order_by(DeductionLog.created_at.desc())
    )

    return result.scalars().all()