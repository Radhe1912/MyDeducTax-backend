from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps

router = APIRouter()

@router.post("/calculate")
def calculate_tax(db: Session = Depends(deps.get_db)):
    return {"message": "Tax calculation"}
