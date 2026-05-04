from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
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


from app.db.session import AsyncSessionLocal
import io
import pandas as pd

async def process_file_background(contents: bytes, filename: str, user_id: str):
    import logging
    logger = logging.getLogger(__name__)
    # Parse file
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return
    except Exception as e:
        logger.error(f"Failed to parse file {filename}: {e}")
        return
    
    if df.empty:
        return

    from app.services.csv_parser import transform_df
    parsed_data = transform_df(df)

    if not parsed_data:
        return

    enriched = [classify_expense(e) for e in parsed_data]

    async with AsyncSessionLocal() as db:
        await expense_crud.bulk_insert_transactions(
            db=db,
            user_id=user_id,
            expenses=enriched
        )

@router.post("/upload-file")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    filename = file.filename.lower()

    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV or XLSX files are supported"
        )
        
    contents = await file.read()
    
    # Add to background tasks
    background_tasks.add_task(
        process_file_background,
        contents,
        filename,
        user["user_id"]
    )

    return {
        "message": "File is being processed in the background"
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