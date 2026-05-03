from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional
from app.core.config import settings
import bcrypt


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode("utf-8")[:72]
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
