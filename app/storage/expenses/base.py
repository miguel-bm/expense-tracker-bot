from abc import ABC, abstractmethod
from typing import List

from app.models.expense import Expense


class ExpenseStorageInterface(ABC):
    @abstractmethod
    async def add_expense(self, expense: Expense) -> None:
        pass

    @abstractmethod
    async def update_expense(self, expense: Expense) -> None:
        pass

    @abstractmethod
    async def get_expenses(self) -> List[Expense]:
        pass
