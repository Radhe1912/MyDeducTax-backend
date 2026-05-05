from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.expense import ExpenseCreate
from app.schemas.deduction import DeductionSummary


# ── Business Expenses (for business_owner / freelancer) ──────────────────────
class BusinessExpenses(BaseModel):
    employee_salaries: float = Field(0, ge=0)
    software_subscriptions: float = Field(0, ge=0)
    equipment_hardware: float = Field(0, ge=0)
    office_rent: float = Field(0, ge=0)
    travel_conveyance: float = Field(0, ge=0)
    professional_fees: float = Field(0, ge=0)
    marketing_advertising: float = Field(0, ge=0)
    utilities_internet: float = Field(0, ge=0)
    other_business: float = Field(0, ge=0)

    def total(self) -> float:
        return (
            self.employee_salaries + self.software_subscriptions +
            self.equipment_hardware + self.office_rent +
            self.travel_conveyance + self.professional_fees +
            self.marketing_advertising + self.utilities_internet +
            self.other_business
        )


# ── Main Input ────────────────────────────────────────────────────────────────
class TaxCalculationInput(BaseModel):
    income: float = Field(..., ge=0)
    expenses: List[ExpenseCreate] = Field(default_factory=list)
    employment_type: Optional[str] = "salaried"

    # ── HRA / location
    hra_received: Optional[float] = Field(0, ge=0)
    is_metro: Optional[bool] = True

    # ── Age / family flags
    is_senior_self: Optional[bool] = False
    is_super_senior_self: Optional[bool] = False
    is_senior_parents: Optional[bool] = False
    has_disability: Optional[bool] = False
    has_dependent_disability: Optional[bool] = False

    # ── Section 80C components (combined cap ₹1.5L)
    lic_premium: Optional[float] = Field(0, ge=0)
    ppf_contribution: Optional[float] = Field(0, ge=0)
    epf_contribution: Optional[float] = Field(0, ge=0)
    elss_amount: Optional[float] = Field(0, ge=0)
    nsc_amount: Optional[float] = Field(0, ge=0)
    tuition_fees: Optional[float] = Field(0, ge=0)
    tax_saving_fd: Optional[float] = Field(0, ge=0)
    sukanya_samriddhi: Optional[float] = Field(0, ge=0)
    home_loan_principal: Optional[float] = Field(0, ge=0)   # 80C part

    # ── 80CCD(1B) – NPS self (extra ₹50K on top of 80C)
    nps_self_contribution: Optional[float] = Field(0, ge=0)

    # ── 80D – Health insurance
    health_insurance_self: Optional[float] = Field(0, ge=0)
    health_insurance_parents: Optional[float] = Field(0, ge=0)

    # ── Section 24B – Home loan interest (max ₹2L self-occupied)
    home_loan_interest: Optional[float] = Field(0, ge=0)
    is_self_occupied: Optional[bool] = True

    # ── 80E – Education loan interest (no cap)
    education_loan_interest: Optional[float] = Field(0, ge=0)

    # ── 80EEB – EV loan interest (max ₹1.5L)
    ev_loan_interest: Optional[float] = Field(0, ge=0)

    # ── 80G – Donations
    donations_50pct: Optional[float] = Field(0, ge=0)   # 50 % deductible orgs
    donations_100pct: Optional[float] = Field(0, ge=0)  # 100 % deductible orgs

    # ── 80TTA / 80TTB – Savings / FD interest
    savings_interest: Optional[float] = Field(0, ge=0)

    # ── 80GG – Rent paid (when HRA not received)
    rent_paid_monthly: Optional[float] = Field(0, ge=0)

    # ── HRA Exemption – Rent paid (when HRA IS received, for Sec 10(13A))
    rent_paid_for_hra: Optional[float] = Field(0, ge=0)

    # ── Business expenses (business_owner / freelancer)
    business_expenses: Optional[BusinessExpenses] = None


# ── Sub-results ───────────────────────────────────────────────────────────────
class TaxResult(BaseModel):
    income: float
    taxable_income: float
    total_deduction: float
    tax_payable: float
    regime: str


class BusinessExpenseSummary(BaseModel):
    total: float
    breakdown: dict


# ── API Response ──────────────────────────────────────────────────────────────
class TaxCalculationResponse(BaseModel):
    old_regime: TaxResult
    new_regime: TaxResult
    recommended_regime: str
    savings: float
    deductions: DeductionSummary
    employment_type: Optional[str] = None
    employment_note: Optional[str] = None
    effective_income: Optional[float] = None
    business_expense_summary: Optional[BusinessExpenseSummary] = None