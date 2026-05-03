from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps

router = APIRouter()

@router.get("/")
def get_deductions(db: Session = Depends(deps.get_db)):
    return []
