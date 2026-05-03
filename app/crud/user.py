from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.crud.base import CRUDBase


class CRUDUser(CRUDBase[User]):
    async def get_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


user_crud = CRUDUser(User)