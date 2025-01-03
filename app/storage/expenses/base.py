from abc import ABC, abstractmethod
from typing import List

from app.models.expense import Expense


class ExpenseStorageInterface(ABC):
    @abstractmethod
    def reload_cache(self) -> None:
        pass

    @abstractmethod
    async def add_expense(self, expense: Expense) -> None:
        pass

    @abstractmethod
    async def add_expenses(self, expenses: list[Expense]) -> None:
        pass

    @abstractmethod
    async def update_expense(self, expense: Expense) -> None:
        pass

    @abstractmethod
    async def get_expenses(self, force_reload: bool = False) -> List[Expense]:
        pass
