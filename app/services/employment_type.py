from enum import Enum
from typing import Dict


class EmploymentType(str, Enum):
    SALARIED = "salaried"
    GOVT_EMPLOYEE = "govt_employee"
    BUSINESS_OWNER = "business_owner"
    FREELANCER = "freelancer"


# ======================================================
# EMPLOYMENT TYPE CONFIG
# Each entry describes the rules applicable to that type
# ======================================================

EMPLOYMENT_RULES = {
    EmploymentType.SALARIED: {
        "label": "Salaried",
        "standard_deduction_old": 50000,
        "standard_deduction_new": 50000,
        "hra_eligible": True,
        "lta_eligible": True,
        "nps_employer_pct": 0.10,       # 10% of salary via 80CCD(2)
        "presumptive_tax": False,
        "business_expense_deductible": False,
    },
    EmploymentType.GOVT_EMPLOYEE: {
        "label": "Government Employee",
        "standard_deduction_old": 50000,
        "standard_deduction_new": 50000,
        "hra_eligible": True,
        "lta_eligible": True,
        "nps_employer_pct": 0.14,       # 14% of salary via 80CCD(2) for govt
        "presumptive_tax": False,
        "business_expense_deductible": False,
    },
    EmploymentType.BUSINESS_OWNER: {
        "label": "Business Owner",
        "standard_deduction_old": 0,    # No standard deduction
        "standard_deduction_new": 0,
        "hra_eligible": False,           # Cannot claim HRA
        "lta_eligible": False,
        "nps_employer_pct": 0.10,
        "presumptive_tax": True,
        "presumptive_scheme": "44AD",
        "presumptive_rate": 0.08,       # 8% of turnover (6% digital)
        "business_expense_deductible": True,
    },
    EmploymentType.FREELANCER: {
        "label": "Freelancer / Professional",
        "standard_deduction_old": 0,
        "standard_deduction_new": 0,
        "hra_eligible": False,
        "lta_eligible": False,
        "nps_employer_pct": 0.10,
        "presumptive_tax": True,
        "presumptive_scheme": "44ADA",
        "presumptive_rate": 0.50,       # 50% of gross receipts deemed profit
        "business_expense_deductible": True,
    },
}


def get_employment_rules(employment_type: str) -> Dict:
    """Return the rules dict for the given employment type string."""
    try:
        et = EmploymentType(employment_type)
    except ValueError:
        et = EmploymentType.SALARIED  # Default fallback
    return EMPLOYMENT_RULES[et]


def compute_effective_income(income: float, employment_type: str) -> Dict:
    """
    For business owners and freelancers using presumptive taxation,
    the taxable income is a fraction of total turnover/receipts.
    Returns the effective taxable gross and a note.
    """
    rules = get_employment_rules(employment_type)

    if rules["presumptive_tax"]:
        effective_income = income * rules["presumptive_rate"]
        scheme = rules["presumptive_scheme"]
        rate_pct = int(rules["presumptive_rate"] * 100)
        return {
            "effective_income": effective_income,
            "note": f"Presumptive tax under Section {scheme}: {rate_pct}% of ₹{int(income):,} = ₹{int(effective_income):,} treated as taxable profit.",
            "is_presumptive": True,
            "scheme": scheme,
        }

    return {
        "effective_income": income,
        "note": None,
        "is_presumptive": False,
        "scheme": None,
    }
