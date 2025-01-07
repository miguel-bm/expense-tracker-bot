import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.expense import Expense
from app.storage.expenses.base import ExpenseStorageInterface
from app.storage.google_sheets_mixin import GoogleSheetsMixin
from app.utils.config import settings


class GSpreadExpenseStorage(GoogleSheetsMixin[Expense], ExpenseStorageInterface):
    def __init__(self):
        super().__init__(settings.EXPENSES_SHEET_ID, settings.EXPENSES_SHEET_NAME)

    @property
    def _item_type_name(self) -> str:
        return "expense"

    def _item_to_row(self, expense: Expense) -> list[str | float | bool]:
        return [
            expense.expense_id,
            expense.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            expense.sender,
            expense.cost,
            expense.concept,
            "/".join(expense.category),
            expense.details or "",
            expense.payment_method or "",
            expense.input_method,
            ",".join(expense.tags) if expense.tags else "",
            json.dumps(expense.metadata) if expense.metadata else "",
        ]

    def _record_to_item(self, record: dict) -> Expense:
        return Expense(
            expense_id=str(record["expense_id"]),
            timestamp=datetime.strptime(
                str(record["timestamp"]), "%d/%m/%Y %H:%M:%S"
            ).replace(tzinfo=ZoneInfo("Europe/Madrid")),
            sender=str(record["sender"]),
            cost=float(record["cost"]),
            concept=str(record["concept"]),
            category=str(record["category"]).split("/"),
            details=str(record["details"]) or None,
            payment_method=str(record["payment_method"]) or None,  # type: ignore
            input_method=str(record["input_method"]),  # type: ignore
            tags=str(record["tags"]).split(",") if record["tags"] else None,
            metadata=json.loads(str(record["metadata"]))
            if record["metadata"]
            else None,
        )

    # Interface methods that now use the mixin's implementation
    async def add_expense(self, expense: Expense) -> None:
        await self.add_item(expense)

    async def add_expenses(self, expenses: list[Expense]) -> None:
        await self.add_items(expenses)

    async def update_expense(self, expense: Expense) -> None:
        await self.update_item(expense, "expense_id")

    async def get_expenses(self, force_reload: bool = False) -> list[Expense]:
        return await self.get_items(force_reload)
