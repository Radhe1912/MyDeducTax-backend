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
    regime: str = "new"
) -> Dict:
    """
    Production-ready tax calculation.

    Parameters:
    - income: total income
    - total_deduction: computed deductions
    - regime: "old" or "new"
    """

    # =========================
    # TAXABLE INCOME
    # =========================
    if regime == "old":
        taxable_income = max(income - total_deduction, 0)
        slabs = OLD_REGIME_SLABS
    else:
        # Standard deduction allowed in new regime (FY 2023-24 onward)
        STANDARD_DEDUCTION = 50000
        taxable_income = max(income - STANDARD_DEDUCTION, 0)
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