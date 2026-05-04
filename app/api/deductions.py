from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.crud.expense import expense_crud
from app.services.csv_parser import parse_file
from app.services.expense_analyzer import classify_expense
from app.services.section_mapper import map_expenses_to_sections
from app.services.deduction_engine import compute_deductions
from app.models.tax_section import TaxSection
from app.models.expense import Expense

router = APIRouter()


@router.get("/my-expenses")
async def get_user_expenses(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    return await expense_crud.get_by_user(db, user["user_id"])


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    filename = file.filename.lower()

    # =========================
    # VALIDATION
    # =========================
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV or XLSX files are supported"
        )

    # =========================
    # PARSE FILE
    # =========================
    try:
        parsed_data = await parse_file(file)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File parsing failed: {str(e)}"
        )

    if not parsed_data:
        return {"message": "No valid transactions found"}

    # =========================
    # CLASSIFY
    # =========================
    enriched = [classify_expense(e) for e in parsed_data]

    # =========================
    # STORE WITH DEDUPLICATION
    # =========================
    inserted_count = await expense_crud.bulk_insert_transactions(
        db=db,
        user_id=user["user_id"],
        expenses=enriched
    )

    return {
        "message": "File processed successfully",
        "transactions_received": len(enriched),
        "transactions_inserted": inserted_count
    }


@router.get("/breakdown")
async def get_deduction_breakdown(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    # =========================
    # FETCH EXPENSES
    # =========================
    result = await db.execute(
        select(Expense).where(Expense.user_id == user["user_id"])
    )
    expenses = result.scalars().all()

    if not expenses:
        return {"total_sections": 0, "deductions": []}

    expense_list = [
        {
            "id": str(e.id),
            "amount": float(e.amount),
            "category": e.category,
            "sub_category": e.sub_category,
            "description": e.description
        }
        for e in expenses
    ]

    # =========================
    # FETCH SECTIONS
    # =========================
    section_result = await db.execute(select(TaxSection))
    sections = section_result.scalars().all()

    if not sections:
        return {"total_sections": 0, "deductions": []}

    # =========================
    # 🔴 FIX: PASS SECTIONS INTO MAPPER
    # =========================
    expense_map = map_expenses_to_sections(
        expenses=expense_list,
        sections=sections
    )

    if not expense_map:
        return {
            "total_sections": 0,
            "deductions": [],
            "debug": "No mapping created"
        }

    # =========================
    # DEDUCTION ENGINE
    # =========================
    deductions = await compute_deductions(
        expense_map,
        sections,
        context={}
    )

    return deductions