from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from app.api.deps import get_db, get_current_user
from app.schemas.tax import TaxCalculationInput, TaxCalculationResponse, BusinessExpenseSummary

from app.services.expense_analyzer import classify_expense
from app.services.section_mapper import map_expenses_to_sections
from app.services.deduction_engine import compute_deductions
from app.services.direct_deductions import compute_direct_deductions, compute_business_expense_summary
from app.services.tax_calculator import calculate_tax
from app.services.recommendation import generate_recommendations
from app.services.employment_type import get_employment_rules, compute_effective_income

from app.models.tax_section import TaxSection
from app.models.report import TaxResult
from app.core.rate_limit import limiter
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("audit")


def _merge_deductions(engine_list, direct_list):
    """
    Merge expense-engine deductions with structured-form deductions.
    For sections that appear in both, sum amounts and re-apply cap.
    """
    CAPS = {
        "80C": 150_000,
        "80D": None,   # variable, handled per-entry
    }
    merged: dict = {}
    for d in engine_list + direct_list:
        key = d["section"]
        if key in merged:
            merged[key]["amount"] += d["amount"]
            if merged[key]["limit"] and merged[key]["amount"] > merged[key]["limit"]:
                merged[key]["amount"] = merged[key]["limit"]
                merged[key]["remaining"] = 0
        else:
            merged[key] = dict(d)
    return list(merged.values())


@router.post("/calculate", response_model=TaxCalculationResponse)
@limiter.limit("10/minute")
async def calculate_tax_endpoint(
    request: Request,
    data: TaxCalculationInput,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    emp_type = data.employment_type or "salaried"
    emp_rules = get_employment_rules(emp_type)

    logger.info(
        f"User {user['user_id']} | income={data.income} | "
        f"emp={emp_type} | expenses={len(data.expenses or [])}"
    )

    # ── 1. EFFECTIVE INCOME (presumptive for business/freelancer) ──────────────
    effective_income_data = compute_effective_income(data.income, emp_type)
    effective_income = effective_income_data["effective_income"]

    # ── 2. ENRICH EXPENSES from imported bank transactions ─────────────────────
    enriched_expenses = [classify_expense(e.dict()) for e in (data.expenses or [])]

    # Business/freelancer can't claim HRA from bank-imported rent rows
    if not emp_rules["hra_eligible"]:
        enriched_expenses = [e for e in enriched_expenses if e.get("category") != "rent"]

    # ── 3. LOAD SECTIONS from DB ───────────────────────────────────────────────
    sections = (await db.execute(select(TaxSection))).scalars().all()

    # ── 4. MAP EXPENSES → TAX SECTIONS ────────────────────────────────────────
    expense_map = map_expenses_to_sections(enriched_expenses, sections)

    # ── 5. EXPENSE-ENGINE DEDUCTIONS ──────────────────────────────────────────
    engine_result = await compute_deductions(
        expense_map,
        sections,
        context={
            "salary": effective_income,
            "hra_received": data.hra_received if emp_rules["hra_eligible"] else 0,
            "is_metro": data.is_metro,
            "is_senior_self": data.is_senior_self,
            "is_super_senior_self": data.is_super_senior_self,
            "is_senior_parents": data.is_senior_parents,
            "has_disability": data.has_disability,
            "has_dependent_disability": data.has_dependent_disability,
            "employment_type": emp_type,
            "nps_employer_pct": emp_rules["nps_employer_pct"],
        },
    )
    engine_deductions = engine_result["deductions"]

    # ── 6. STRUCTURED / FORM DEDUCTIONS ───────────────────────────────────────
    direct_deductions = compute_direct_deductions(data)

    # ── 7. MERGE BOTH SOURCES ─────────────────────────────────────────────────
    all_deductions = _merge_deductions(engine_deductions, direct_deductions)
    total_deduction = sum(d["amount"] for d in all_deductions)

    # ── 8. BUSINESS EXPENSE SUMMARY (informational for biz/freelancer) ────────
    biz_summary = None
    if data.business_expenses and emp_type in ("business_owner", "freelancer"):
        biz_bd = compute_business_expense_summary(data.business_expenses)
        biz_total = data.business_expenses.total()
        biz_summary = BusinessExpenseSummary(total=biz_total, breakdown=biz_bd)

    # ── 9. TAX CALCULATION BOTH REGIMES ───────────────────────────────────────
    tax_result_new = calculate_tax(
        income=effective_income,
        total_deduction=total_deduction,
        regime="new",
        is_senior_self=data.is_senior_self,
        is_super_senior_self=data.is_super_senior_self,
        employment_type=emp_type,
    )
    tax_result_old = calculate_tax(
        income=effective_income,
        total_deduction=total_deduction,
        regime="old",
        is_senior_self=data.is_senior_self,
        is_super_senior_self=data.is_super_senior_self,
        employment_type=emp_type,
    )

    new_tax = tax_result_new["total_tax"]
    old_tax = tax_result_old["total_tax"]
    recommended = "new" if new_tax < old_tax else "old"
    savings = abs(new_tax - old_tax)

    # ── 10. RECOMMENDATIONS ───────────────────────────────────────────────────
    recommendations = generate_recommendations(all_deductions)

    # ── 11. BUILD RESPONSE ────────────────────────────────────────────────────
    final_response = {
        "old_regime": {
            "income": effective_income,
            "taxable_income": tax_result_old["taxable_income"],
            "total_deduction": total_deduction,
            "tax_payable": old_tax,
            "regime": "old",
        },
        "new_regime": {
            "income": effective_income,
            "taxable_income": tax_result_new["taxable_income"],
            "total_deduction": total_deduction,
            "tax_payable": new_tax,
            "regime": "new",
        },
        "recommended_regime": recommended,
        "savings": savings,
        "deductions": {
            "sections": all_deductions,
            "recommendations": recommendations,
            "total_deduction": total_deduction,
        },
        "employment_type": emp_type,
        "employment_note": effective_income_data.get("note"),
        "effective_income": effective_income,
        "business_expense_summary": biz_summary,
    }

    # ── 12. PERSIST REPORT ────────────────────────────────────────────────────
    db.add(TaxResult(
        user_id=user["user_id"],
        income=data.income,
        total_deduction=total_deduction,
        tax_payable=new_tax if recommended == "new" else old_tax,
        regime=recommended,
        breakdown=json.dumps(final_response["deductions"]),
        created_at=datetime.utcnow(),
    ))
    await db.commit()

    return final_response