"""
direct_deductions.py
────────────────────
Computes structured tax deductions from form inputs (not from DB-expense classification).
Returns a list of SectionDeduction-compatible dicts + total.
"""
from typing import List, Dict, Any


def _entry(section: str, amount: float, limit=None, remaining=None) -> Dict:
    return {
        "section": section,
        "amount": round(amount, 2),
        "count": 1,
        "limit": limit,
        "remaining": round(remaining, 2) if remaining is not None else None,
    }


def compute_direct_deductions(data) -> List[Dict]:
    """
    data: TaxCalculationInput instance
    Returns list of deduction dicts ready to be merged with expense-engine results.
    """
    deductions: List[Dict] = []
    is_senior = data.is_senior_self or data.is_super_senior_self

    # ──────────────────────────────────────────────────────
    # HRA EXEMPTION  – Section 10(13A)
    #   Only for salaried / govt employees who receive HRA
    #   Exemption = min of:
    #     a) HRA actually received
    #     b) 50% of salary (metro) or 40% (non-metro)
    #     c) Rent paid – 10% of salary
    # ──────────────────────────────────────────────────────
    emp_type_hra = data.employment_type or "salaried"
    hra_received = data.hra_received or 0
    rent_for_hra = (data.rent_paid_for_hra or 0) * 12  # monthly → annual
    salary = data.income

    if (
        emp_type_hra in ("salaried", "govt_employee")
        and hra_received > 0
        and rent_for_hra > 0
        and salary > 0
    ):
        pct = 0.50 if data.is_metro else 0.40
        hra_exempt = min(
            hra_received,
            pct * salary,
            max(rent_for_hra - 0.10 * salary, 0),
        )
        if hra_exempt > 0:
            deductions.append(_entry("HRA Exemption (Sec 10(13A))", hra_exempt, None, None))

    # ──────────────────────────────────────────────────────
    # SECTION 80C  (combined cap ₹1,50,000)
    # ──────────────────────────────────────────────────────
    CAP_80C = 150_000
    raw_80c = (
        (data.lic_premium or 0)
        + (data.ppf_contribution or 0)
        + (data.epf_contribution or 0)
        + (data.elss_amount or 0)
        + (data.nsc_amount or 0)
        + (data.tuition_fees or 0)
        + (data.tax_saving_fd or 0)
        + (data.sukanya_samriddhi or 0)
        + (data.home_loan_principal or 0)
    )
    if raw_80c > 0:
        capped = min(raw_80c, CAP_80C)
        deductions.append(_entry("80C", capped, CAP_80C, max(0, CAP_80C - capped)))

    # ──────────────────────────────────────────────────────
    # 80CCD(1B)  – NPS self, extra ₹50,000 beyond 80C
    # ──────────────────────────────────────────────────────
    CAP_NPS = 50_000
    nps = data.nps_self_contribution or 0
    if nps > 0:
        capped = min(nps, CAP_NPS)
        deductions.append(_entry("80CCD(1B) NPS", capped, CAP_NPS, max(0, CAP_NPS - capped)))

    # ──────────────────────────────────────────────────────
    # 80D  – Health insurance
    #   Self/family: ₹25K (₹50K if senior self)
    #   Parents:     ₹25K (₹50K if senior parents)
    #   Split into TWO entries so recommendations are precise.
    # ──────────────────────────────────────────────────────
    self_limit = 50_000 if is_senior else 25_000
    par_limit  = 50_000 if data.is_senior_parents else 25_000

    health_self = min(data.health_insurance_self or 0, self_limit)
    health_par  = min(data.health_insurance_parents or 0, par_limit)

    if health_self > 0 or (data.health_insurance_self or 0) > 0:
        # Always add self entry if they entered any amount (to show the cap)
        entered_self = data.health_insurance_self or 0
        if entered_self > 0:
            deductions.append(_entry(
                "80D Self & Family Health Insurance",
                health_self,
                self_limit,
                max(0, self_limit - health_self),
            ))

    if health_par > 0 or (data.health_insurance_parents or 0) > 0:
        entered_par = data.health_insurance_parents or 0
        if entered_par > 0:
            deductions.append(_entry(
                "80D Parents Health Insurance",
                health_par,
                par_limit,
                max(0, par_limit - health_par),
            ))

    # Show parents' unused slot as a separate tip entry (₹0 deduction, full remaining)
    # so the recommendation engine can suggest it even if no parents premium was entered
    if (data.health_insurance_parents or 0) == 0 and health_self > 0:
        # Parents slot completely unused — show as ₹0 deduction with full remaining
        # so recommendation engine picks it up
        deductions.append(_entry(
            "80D Parents Health Insurance",
            0,
            par_limit,
            par_limit,
        ))

    # ──────────────────────────────────────────────────────
    # SECTION 24B  – Home loan interest
    #   Self-occupied: max ₹2,00,000
    #   Let-out property: entire interest deductible (set limit=None)
    # ──────────────────────────────────────────────────────
    hl_interest = data.home_loan_interest or 0
    if hl_interest > 0:
        if data.is_self_occupied:
            CAP_24B = 200_000
            capped  = min(hl_interest, CAP_24B)
            deductions.append(_entry("Sec 24B Home Loan Interest", capped, CAP_24B, max(0, CAP_24B - capped)))
        else:
            # Let-out: full interest, no cap
            deductions.append(_entry("Sec 24B Home Loan Interest (Let-out)", hl_interest, None, None))

    # ──────────────────────────────────────────────────────
    # 80E  – Education loan interest (no limit, 8 years)
    # ──────────────────────────────────────────────────────
    edu = data.education_loan_interest or 0
    if edu > 0:
        deductions.append(_entry("80E Education Loan Interest", edu, None, None))

    # ──────────────────────────────────────────────────────
    # 80EEB  – EV loan interest (max ₹1,50,000)
    # ──────────────────────────────────────────────────────
    CAP_EV = 150_000
    ev = data.ev_loan_interest or 0
    if ev > 0:
        capped = min(ev, CAP_EV)
        deductions.append(_entry("80EEB EV Loan Interest", capped, CAP_EV, max(0, CAP_EV - capped)))

    # ──────────────────────────────────────────────────────
    # 80G  – Donations
    # ──────────────────────────────────────────────────────
    don50 = data.donations_50pct or 0
    don100 = data.donations_100pct or 0
    if don50 > 0:
        deductions.append(_entry("80G Donation (50%)", don50 * 0.5, None, None))
    if don100 > 0:
        deductions.append(_entry("80G Donation (100%)", don100, None, None))

    # ──────────────────────────────────────────────────────
    # 80TTA / 80TTB  – Savings / FD interest
    #   General: savings a/c only, cap ₹10,000  (80TTA)
    #   Senior:  savings + FD, cap ₹50,000       (80TTB)
    # ──────────────────────────────────────────────────────
    interest = data.savings_interest or 0
    if interest > 0:
        if is_senior:
            capped = min(interest, 50_000)
            deductions.append(_entry("80TTB Senior Interest Income", capped, 50_000, max(0, 50_000 - capped)))
        else:
            capped = min(interest, 10_000)
            deductions.append(_entry("80TTA Savings Interest", capped, 10_000, max(0, 10_000 - capped)))

    # ──────────────────────────────────────────────────────
    # 80GG  – Rent paid when HRA not received
    #   Deduction = min(₹5000/month, 25% of income, rent-10% of income)
    #   Only for those NOT receiving HRA component
    # ──────────────────────────────────────────────────────
    emp_type = data.employment_type or "salaried"
    hrv = data.hra_received or 0
    rent_monthly = data.rent_paid_monthly or 0
    if rent_monthly > 0 and hrv == 0 and emp_type not in ("business_owner", "freelancer"):
        annual_rent = rent_monthly * 12
        income = data.income
        option1 = 5_000 * 12            # ₹60,000
        option2 = 0.25 * income
        option3 = max(annual_rent - 0.10 * income, 0)
        ded_80gg = min(option1, option2, option3)
        if ded_80gg > 0:
            deductions.append(_entry("80GG Rent Paid", ded_80gg, 60_000, None))

    # ──────────────────────────────────────────────────────
    # 80U / 80DD  (already handled by deduction_engine context flags)
    # (kept here for reference — NOT added again to avoid double-count)
    # ──────────────────────────────────────────────────────

    return deductions


def compute_business_expense_summary(be) -> dict:
    """Returns breakdown dict for the API response."""
    if be is None:
        return {}
    return {
        "Employee Salaries":         be.employee_salaries,
        "Software Subscriptions":    be.software_subscriptions,
        "Equipment & Hardware":      be.equipment_hardware,
        "Office Rent":               be.office_rent,
        "Travel & Conveyance":       be.travel_conveyance,
        "Professional Fees":         be.professional_fees,
        "Marketing & Advertising":   be.marketing_advertising,
        "Utilities & Internet":      be.utilities_internet,
        "Other Business Expenses":   be.other_business,
    }
