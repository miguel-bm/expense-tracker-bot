from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Income(BaseModel):
    income_id: str
    timestamp: datetime
    sender: str
    value: float
    concept: str
    category: list[str]
    details: str | None = None
    payment_method: Literal["cash", "card", "transfer", "p2p"] | None = None
    input_method: Literal["manual", "bot", "etl"] = "bot"
    tags: list[str] | None = None
    metadata: dict | None = None
