from typing import Dict, List


# =========================
# TAX CONFIG (FY 2023-24 / 2024-25 baseline)
# =========================

OLD_REGIME_SLABS = [
    (250000, 0.0),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]

NEW_REGIME_SLABS = [
    (300000, 0.0),
    (600000, 0.05),
    (900000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float("inf"), 0.30),
]

CESS_RATE = 0.04  # 4%


# =========================
# CORE SLAB CALCULATION
# =========================

def compute_slab_tax(income: float, slabs: List):
    tax = 0
    prev_limit = 0

    for limit, rate in slabs:
        if income > limit:
            taxable_amount = limit - prev_limit
            tax += taxable_amount * rate
            prev_limit = limit
        else:
            taxable_amount = income - prev_limit
            tax += taxable_amount * rate
            break

    return tax


# =========================
# REBATE (SECTION 87A)
# =========================

def apply_rebate(tax: float, taxable_income: float, regime: str):
    """
    FY 2023-24:
    - Old regime: rebate if income <= 5L
    - New regime: rebate if income <= 7L
    """

    if regime == "old" and taxable_income <= 500000:
        return min(tax, 12500)

    if regime == "new" and taxable_income <= 700000:
        return tax  # full rebate (effectively zero tax)

    return 0


# =========================
# SURCHARGE (BASIC VERSION)
# =========================

def apply_surcharge(tax: float, income: float):
    """
    Simplified surcharge logic.
    Extend later if needed.
    """

    if income > 50000000:  # >5 Cr
        return tax * 0.37
    elif income > 20000000:  # >2 Cr
        return tax * 0.25
    elif income > 10000000:  # >1 Cr
        return tax * 0.15
    elif income > 5000000:  # >50L
        return tax * 0.10

    return 0


# =========================
# MAIN TAX FUNCTION
# =========================

def calculate_tax(
    income: float,
    total_deduction: float,
    regime: str = "new",
    is_senior_self: bool = False,
    is_super_senior_self: bool = False,
    employment_type: str = "salaried",
) -> Dict:
    """
    Production-ready tax calculation with employment type awareness.
    """
    from app.services.employment_type import get_employment_rules
    rules = get_employment_rules(employment_type)

    # =========================
    # TAXABLE INCOME
    # =========================
    if regime == "old":
        std_ded = rules["standard_deduction_old"]
        taxable_income = max(income - total_deduction - std_ded, 0)
        
        # Adjust slabs for seniors
        if is_super_senior_self:
            slabs = [
                (500000, 0.0),
                (1000000, 0.20),
                (float("inf"), 0.30),
            ]
        elif is_senior_self:
            slabs = [
                (300000, 0.0),
                (500000, 0.05),
                (1000000, 0.20),
                (float("inf"), 0.30),
            ]
        else:
            slabs = OLD_REGIME_SLABS
            
    else:
        std_ded = rules["standard_deduction_new"]
        taxable_income = max(income - std_ded, 0)
        slabs = NEW_REGIME_SLABS

    # =========================
    # BASE TAX
    # =========================
    base_tax = compute_slab_tax(taxable_income, slabs)

    # =========================
    # REBATE
    # =========================
    rebate = apply_rebate(base_tax, taxable_income, regime)
    tax_after_rebate = max(base_tax - rebate, 0)

    # =========================
    # SURCHARGE
    # =========================
    surcharge = apply_surcharge(tax_after_rebate, income)

    # =========================
    # CESS
    # =========================
    cess = (tax_after_rebate + surcharge) * CESS_RATE

    # =========================
    # FINAL TAX
    # =========================
    total_tax = tax_after_rebate + surcharge + cess

    return {
        "regime": regime,
        "income": income,
        "taxable_income": taxable_income,
        "base_tax": base_tax,
        "rebate": rebate,
        "surcharge": surcharge,
        "cess": cess,
        "total_tax": total_tax
    }