from app.crud.base import CRUDBase
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate

class CRUDExpense(CRUDBase[Expense, ExpenseCreate, ExpenseCreate]):
    pass

expense = CRUDExpense(Expense)
