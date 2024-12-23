import uuid
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
    input_method: Literal["manual", "bot", "form"] = "bot"
    details: str | None = None
    payment_method: str | None = None
    receipt_url: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None

    async def call(self, response_context: ResponseContext) -> str:
        expense_id = str(uuid.uuid4())
        expense_timestamp = (
            datetime.fromisoformat(self.timestamp)
            if self.timestamp
            else datetime.now(timezone.utc)
        )
        expense = Expense(
            expense_id=expense_id,
            timestamp=expense_timestamp,
            sender=self.sender,
            cost=self.cost,
            concept=self.concept,
            category=self.category,
            input_method=self.input_method,
            is_recurring=False,
            details=self.details,
            payment_method=self.payment_method,
            receipt_url=self.receipt_url,
            tags=self.tags,
            metadata=self.metadata,
        )
        await response_context.storage.add_expense(expense)
        return f"Expense created successfully with id {expense_id}"
