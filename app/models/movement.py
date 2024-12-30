from datetime import date
from random import randint

from pydantic import BaseModel, Field


class Movement(BaseModel):
    movement_id: str = Field(default_factory=lambda: hex(randint(0, 0xFFFFFFFF))[2:10])
    date_: date
    date_value: date
    description: str
    amount: float
    balance: float

    @property
    def is_expense(self) -> bool:
        return self.amount < 0

    @property
    def is_income(self) -> bool:
        return self.amount > 0

    @property
    def min_date(self) -> date:
        return min(self.date_, self.date_value)
