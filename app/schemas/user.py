from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"