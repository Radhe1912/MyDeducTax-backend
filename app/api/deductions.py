from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.crud.expense import expense_crud
from app.services.csv_parser import parse_csv
from app.services.expense_analyzer import classify_expense

from app.services.section_mapper import map_expenses_to_sections
from app.services.deduction_engine import compute_deductions
from app.models.tax_section import TaxSection
from sqlalchemy import select
from app.models.expense import Expense

router = APIRouter()

@router.get("/my-expenses")
async def get_user_expenses(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    return await expense_crud.get_by_user(db, user["user_id"])

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")

    # =========================
    # STEP 1: Parse CSV
    # =========================
    try:
        parsed_data = parse_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV parsing failed: {str(e)}")

    if not parsed_data:
        return {"message": "No valid transactions found"}

    # =========================
    # STEP 2: Classify
    # =========================
    enriched = [classify_expense(e) for e in parsed_data]

    # =========================
    # STEP 3: Store (bulk)
    # =========================
    await expense_crud.bulk_insert_transactions(
        db=db,
        user_id=user["user_id"],
        expenses=enriched
    )

    return {
        "message": "CSV processed successfully",
        "transactions_processed": len(enriched)
    }

@router.get("/breakdown")
async def get_deduction_breakdown(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    # get user expenses
    result = await db.execute(
        select(Expense).where(Expense.user_id == user["user_id"])
    )
    expenses = result.scalars().all()

    if not expenses:
        return {"message": "No expenses found"}

    # convert to dict format
    expense_list = [
        {
            "id": str(e.id),
            "amount": e.amount,
            "category": e.category,
            "sub_category": e.sub_category
        }
        for e in expenses
    ]

    # load sections
    sections = (await db.execute(select(TaxSection))).scalars().all()

    expense_map = map_expenses_to_sections(expense_list)

    deductions = await compute_deductions(
        expense_map,
        sections,
        context={}
    )

    return deductions