from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from app.models.expense import Expense


class StorageInterface(ABC):
    @abstractmethod
    async def add_expense(self, expense: Expense) -> str:
        """Add an expense and return its ID"""
        pass

    @abstractmethod
    async def update_expense(self, expense_id: str, expense: Expense) -> None:
        """Update an existing expense"""
        pass

    @abstractmethod
    async def get_expenses(
        self, start_date: datetime, end_date: datetime
    ) -> List[Expense]:
        """Get expenses within a date range"""
        pass
