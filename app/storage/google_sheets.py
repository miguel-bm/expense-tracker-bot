import json
from datetime import datetime
from typing import List

from gspread.auth import service_account

from app.models.expense import Expense
from app.storage.base import StorageInterface
from app.utils.config import settings

SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GSpreadStorage(StorageInterface):
    def __init__(self):
        self._client = service_account(
            filename=settings.GOOGLE_SHEETS_CREDENTIALS,
            scopes=[SCOPE],
        )
        self._sheet = self._client.open_by_key(settings.EXPENSES_SHEET_ID)
        self._expenses_worksheet = self._sheet.worksheet("expenses")

    def _expense_to_row(self, expense: Expense) -> list[str | float | bool]:
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
            expense.is_recurring,
            expense.receipt_url or "",
            ",".join(expense.tags) if expense.tags else "",
            json.dumps(expense.metadata) if expense.metadata else "",
        ]

    async def add_expense(self, expense: Expense) -> None:
        row = self._expense_to_row(expense)
        self._expenses_worksheet.append_row(row)

    async def update_expense(self, expense: Expense) -> None:
        cell = self._expenses_worksheet.find(expense.expense_id, in_column=1)
        if not cell:
            raise ValueError(f"Expense with ID {expense.expense_id} not found")

        range_name = f"A{cell.row}:N{cell.row}"
        updated_row = self._expense_to_row(expense)

        self._expenses_worksheet.update(range_name=range_name, values=[updated_row])

    async def get_expenses(self) -> List[Expense]:
        # Get all records
        records = self._expenses_worksheet.get_all_records()
        expenses = []

        for record in records:
            timestamp = datetime.strptime(str(record["timestamp"]), "%d/%m/%Y %H:%M:%S")
            expenses.append(
                Expense(
                    expense_id=str(record["expense_id"]),
                    timestamp=timestamp,
                    sender=str(record["sender"]),
                    cost=float(record["cost"]),
                    concept=str(record["concept"]),
                    category=str(record["category"]).split("/"),
                    details=str(record["details"]) or None,
                    payment_method=str(record["payment_method"]) or None,
                    input_method=str(record["input_method"]),  # type: ignore
                    is_recurring=str(record["is_recurring"]) == "TRUE",
                    receipt_url=str(record["receipt_url"]) or None,
                    tags=str(record["tags"]).split(",") if record["tags"] else None,
                    metadata=json.loads(str(record["metadata"]))
                    if record["metadata"]
                    else None,
                )
            )
        return expenses
