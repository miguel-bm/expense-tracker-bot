from dataclasses import dataclass
from datetime import date


@dataclass
class Movement:
    date_: date
    date_value: date
    description: str
    amount: float
    balance: float
