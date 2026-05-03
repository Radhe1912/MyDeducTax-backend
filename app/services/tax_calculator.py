class TaxCalculator:
    def calculate_tax(self, income: float, deductions: float) -> float:
        taxable = max(0, income - deductions)
        return taxable * 0.1 # dummy 10% rate
