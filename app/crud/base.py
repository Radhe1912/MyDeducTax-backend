from typing import Type, TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

ModelType = TypeVar("ModelType")


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id):
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: dict):
        obj = self.model(**obj_in)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def bulk_create(self, db: AsyncSession, objs: List[dict]):
        objects = [self.model(**obj) for obj in objs]
        db.add_all(objects)
        await db.commit()
        return objects

    async def delete(self, db: AsyncSession, id):
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj