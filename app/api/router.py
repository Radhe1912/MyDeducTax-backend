from fastapi import APIRouter
from app.api import auth, tax, deductions, reports, expenses

router = APIRouter()

router.include_router(auth.router)
router.include_router(tax.router)
router.include_router(deductions.router)
router.include_router(reports.router)
router.include_router(expenses.router)