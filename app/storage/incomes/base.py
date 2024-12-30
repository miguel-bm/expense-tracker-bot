from abc import ABC, abstractmethod

from app.models.income import Income


class IncomeStorageInterface(ABC):
    @abstractmethod
    async def add_income(self, income: Income) -> None:
        pass

    @abstractmethod
    async def add_incomes(self, incomes: list[Income]) -> None:
        pass

    @abstractmethod
    async def update_income(self, income: Income) -> None:
        pass

    @abstractmethod
    async def get_incomes(self, force_reload: bool = False) -> list[Income]:
        pass
