from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from app.api.deps import get_db, get_current_user
from app.schemas.tax import TaxCalculationInput, TaxCalculationResponse

from app.services.expense_analyzer import classify_expense
from app.services.section_mapper import map_expenses_to_sections
from app.services.deduction_engine import compute_deductions
from app.services.tax_calculator import calculate_tax
from app.services.recommendation import generate_recommendations

from app.models.tax_section import TaxSection
from app.models.report import Report  # ✅ IMPORTANT

router = APIRouter()

@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_tax_endpoint(
    data: TaxCalculationInput,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # ======================
    # 1. ENRICH EXPENSES
    # ======================
    enriched_expenses = [
        classify_expense(e.dict()) for e in data.expenses
    ]

    # ======================
    # 2. LOAD SECTIONS
    # ======================
    sections = (await db.execute(select(TaxSection))).scalars().all()

    # ======================
    # 3. MAP EXPENSES
    # ======================
    expense_map = map_expenses_to_sections(enriched_expenses, sections)

    # ======================
    # 4. COMPUTE DEDUCTIONS
    # ======================
    engine_result = await compute_deductions(
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

    total_deduction = engine_result["total_deduction"]
    sections_list = engine_result["deductions"]

    # ======================
    # 5. TAX CALCULATION
    # ======================
    tax_result = calculate_tax(
        income=data.income,
        total_deduction=total_deduction,
        regime="new",
    )

    # ======================
    # 6. RECOMMENDATIONS
    # ======================
    recommendations = generate_recommendations(sections_list)

    # ======================
    # FINAL RESPONSE OBJECT
    # ======================
    final_response = {
        "tax": {
            "income": data.income,
            "taxable_income": tax_result["taxable_income"],
            "total_deduction": total_deduction,
            "tax_payable": tax_result["total_tax"],
        },
        "deductions": {
            "sections": sections_list,
            "recommendations": recommendations,
            "total_deduction": total_deduction,
        },
    }

    # ======================
    # 7. SAVE REPORT (FIXED)
    # ======================
    report = Report(
        user_id=user["user_id"],
        income=data.income,
        total_deduction=total_deduction,
        tax_payable=tax_result["total_tax"],
        breakdown=json.dumps(final_response["deductions"]),
        created_at=datetime.utcnow()
    )

    db.add(report)
    await db.commit()

    # ======================
    # 8. RETURN RESPONSE
    # ======================
    return final_response