from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    APP_NAME: str = "MyDeducTax"
    DEBUG: bool = True

    REDIS_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()