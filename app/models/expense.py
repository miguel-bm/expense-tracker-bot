from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Expense(BaseModel):
    expense_id: str
    timestamp: datetime
    sender: str
    cost: float
    concept: str
    category: list[str]
    details: str | None = None
    payment_method: Literal["cash", "card", "transfer", "p2p"] | None = None
    input_method: Literal["manual", "bot", "form"] = "bot"
    tags: list[str] | None = None
    metadata: dict | None = None
