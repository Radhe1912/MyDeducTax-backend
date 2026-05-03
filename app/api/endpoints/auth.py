from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps

router = APIRouter()

@router.post("/login")
def login(db: Session = Depends(deps.get_db)):
    return {"message": "Login endpoint"}

@router.post("/register")
def register(db: Session = Depends(deps.get_db)):
    return {"message": "Register endpoint"}
