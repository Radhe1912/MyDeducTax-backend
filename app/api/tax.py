from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.tax import TaxCalculationInput, TaxCalculationResponse

from app.services.expense_analyzer import classify_expense
from app.services.section_mapper import map_expenses_to_sections, load_tax_sections
from app.services.deduction_engine import compute_deductions
from app.services.tax_calculator import calculate_tax
from app.services.recommendation import generate_recommendations

router = APIRouter()


@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_tax_endpoint(
    data: TaxCalculationInput,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # =========================
    # STEP 1: Normalize + classify
    # =========================
    enriched_expenses = [classify_expense(e.dict()) for e in data.expenses]

    # =========================
    # STEP 2: Section mapping
    # =========================
    expense_map = await map_expenses_to_sections(enriched_expenses, db)

    sections = await load_tax_sections(db)

    # =========================
    # STEP 3: Deduction engine
    # =========================
    deductions = await compute_deductions(
        expense_map,
        sections,
        context={
            "salary": data.income,
            "hra_received": data.hra_received,
            "is_metro": data.is_metro,
            "is_senior_self": data.is_senior_self,
            "is_senior_parents": data.is_senior_parents,
        },
    )
    total_deduction = sum(d["total_allowed"] for d in deductions)

    # =========================
    # STEP 4: Tax calculation
    # =========================
    tax_result = calculate_tax(
        income=data.income,
        total_deduction=total_deduction,
        regime="new",  # later: dynamic
    )

    # =========================
    # STEP 5: Recommendations
    # =========================
    recommendations = generate_recommendations(deductions)

    return {
        "tax": {
            "income": data.income,
            "taxable_income": tax_result["taxable_income"],
            "total_deduction": total_deduction,
            "tax_payable": tax_result["total_tax"],
        },
        "deductions": {
            "sections": deductions,
            "recommendations": recommendations,
            "total_deduction": total_deduction,
        },
    }
