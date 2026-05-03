from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_db, get_current_user
from app.crud.user import user_crud

router = APIRouter()

@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return user

@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await user_crud.get_by_email(db, user.email)

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = await user_crud.create(db, {
        "email": user.email,
        "hashed_password": hash_password(user.password),
        "full_name": user.full_name
    })

    return {"message": "User created", "user_id": str(new_user.id)}


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await user_crud.get_by_email(db, user.email)

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": str(db_user.id)})

    return {"access_token": token}