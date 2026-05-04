from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter

from app.api.router import router as api_router
from app.core.logging import setup_logging
from app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    print("🚀 Starting MyDeducTax backend...")
    await init_db()
    print("✅ Database initialized")
    yield
    print("🛑 Shutting down...")

app = FastAPI(
    title="MyDeducTax API",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "MyDeducTax API is running"}