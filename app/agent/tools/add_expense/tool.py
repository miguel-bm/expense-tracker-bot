import hashlib
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field

from app.agent.tools.base import BaseTool, ResponseContext
from app.models.expense import Expense


class AddExpense(BaseTool):
    """Add an expense to the database."""

    timestamp: str | None = Field(
        default=None,
        description="The timestamp of the expense in ISO format. Defaults to the current timestamp.",
    )
    sender: str = Field(description="The name of the user that sent the expense.")
    cost: float
    concept: str
    category: list[str]
    payment_method: Literal["cash", "card", "transfer", "p2p"]
    details: str | None = None
    receipt_url: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None

    def _generate_expense_id(self, expense_timestamp: datetime) -> str:
        fields_to_hash = (
            expense_timestamp.isoformat(),
            str(self.cost),
            str(self.concept),
            str(self.category),
            str(self.payment_method),
        )
        return hashlib.sha256(";".join(fields_to_hash).encode()).hexdigest()[:8]

    async def call(self, response_context: ResponseContext) -> str:
        expense_timestamp = (
            datetime.fromisoformat(self.timestamp)
            if self.timestamp
            else datetime.now(timezone.utc)
        )
        expense_id = self._generate_expense_id(expense_timestamp)
        expense = Expense(
            expense_id=expense_id,
            timestamp=expense_timestamp,
            sender=self.sender,
            cost=self.cost,
            concept=self.concept,
            category=self.category,
            input_method="bot",
            is_recurring=False,
            details=self.details,
            payment_method=self.payment_method,
            receipt_url=self.receipt_url,
            tags=self.tags,
            metadata=self.metadata,
        )
        await response_context.storage.add_expense(expense)
        return f"Expense created successfully with id {expense_id}"
