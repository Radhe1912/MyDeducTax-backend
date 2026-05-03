from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Supabase prefers short-lived connections → avoid aggressive pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # prevents stale connections in serverless environments
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session