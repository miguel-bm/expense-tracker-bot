from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from app.agent.tools.base import BaseTool, ResponseContext
from app.models.expense import Expense


class EditExpense(BaseTool):
    """Edit an expense in the database by providing the expense ID values to update. Any field with null will be left unchanged."""

    expense_id: str
    timestamp: str | None = None
    sender: str | None = None
    cost: float | None = None
    concept: str | None = None
    category: list[str] | None = None
    payment_method: Literal["cash", "card", "transfer", "p2p"] | None = None
    details: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None

    async def call(self, response_context: ResponseContext) -> str:
        expenses = await response_context.storage.get_expenses()
        expense = next((e for e in expenses if e.expense_id == self.expense_id), None)
        if not expense:
            return f"Expense with id {self.expense_id} not found"

        expense_timestamp = (
            datetime.fromisoformat(self.timestamp).replace(
                tzinfo=ZoneInfo("Europe/Madrid")
            )
            if self.timestamp is not None
            else expense.timestamp
        )
        new_expense = Expense(
            expense_id=self.expense_id,
            timestamp=expense_timestamp,
            sender=self.sender if self.sender is not None else expense.sender,
            cost=self.cost if self.cost is not None else expense.cost,
            concept=self.concept if self.concept is not None else expense.concept,
            category=self.category if self.category is not None else expense.category,
            input_method=expense.input_method,
            details=self.details if self.details is not None else expense.details,
            payment_method=self.payment_method
            if self.payment_method is not None
            else expense.payment_method,
            tags=self.tags if self.tags is not None else expense.tags,
            metadata=self.metadata if self.metadata is not None else expense.metadata,
        )

        await response_context.storage.update_expense(new_expense)
        return "Expense updated successfully"
