from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps

router = APIRouter()

@router.get("/generate")
def generate_report(db: Session = Depends(deps.get_db)):
    return {"status": "Report generated"}
