from fastapi import APIRouter
from app.api.endpoints import auth, tax, deductions, reports

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tax.router, prefix="/tax", tags=["tax"])
api_router.include_router(deductions.router, prefix="/deductions", tags=["deductions"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
