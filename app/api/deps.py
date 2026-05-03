from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.session import get_db_session
from app.core.security import decode_access_token

security = HTTPBearer()


async def get_db(db: AsyncSession = Depends(get_db_session)):
    return db


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload