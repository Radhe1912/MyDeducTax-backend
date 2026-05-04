from app.db.base_class import Base
# Import all models here so Alembic can detect them
from app.models.user import User  # noqa
from app.models.expense import Expense  # noqa
from app.models.tax_section import TaxSection  # noqa
from app.models.deduction_log import DeductionLog  # noqa
from app.models.report import TaxResult