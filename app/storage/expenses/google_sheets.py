import json
from datetime import datetime
from zoneinfo import ZoneInfo

from gspread.auth import service_account

from app.models.expense import Expense
from app.storage.expenses.base import ExpenseStorageInterface
from app.utils.config import settings
from app.utils.logger import logger

SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GSpreadExpenseStorage(ExpenseStorageInterface):
    def __init__(self):
        self._client = service_account(settings.GOOGLE_SHEETS_CREDENTIALS, [SCOPE])
        self._sheet = self._client.open_by_key(settings.EXPENSES_SHEET_ID)
        self._expenses_worksheet = self._sheet.worksheet(settings.EXPENSES_SHEET_NAME)
        self.reload_cache()

    @classmethod
    def _expense_to_row(cls, expense: Expense) -> list[str | float | bool]:
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

    @classmethod
    def _record_to_expense(cls, record: dict) -> Expense:
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

    def reload_cache(self) -> None:
        logger.info("Reloading expenses cache")
        records = self._expenses_worksheet.get_all_records(head=1)
        logger.info(f"Found {len(records)} records")
        self._expenses_cache = [self._record_to_expense(record) for record in records]
        self._expenses_cache.sort(key=lambda x: x.timestamp, reverse=False)

    async def add_expense(self, expense: Expense) -> None:
        row = self._expense_to_row(expense)
        self._expenses_worksheet.append_row(row)
        self._expenses_cache.append(expense)
        self._expenses_cache.sort(key=lambda x: x.timestamp, reverse=False)

    async def add_expenses(self, expenses: list[Expense]) -> None:
        rows = [self._expense_to_row(expense) for expense in expenses]
        self._expenses_worksheet.append_rows(rows)
        self._expenses_cache.extend(expenses)
        self._expenses_cache.sort(key=lambda x: x.timestamp, reverse=False)

    async def update_expense(self, expense: Expense) -> None:
        cell = self._expenses_worksheet.find(expense.expense_id, in_column=1)
        if not cell:
            raise ValueError(f"Expense with ID {expense.expense_id} not found")

        range_name = f"A{cell.row}:N{cell.row}"
        updated_row = self._expense_to_row(expense)
        self._expenses_worksheet.update(range_name=range_name, values=[updated_row])
        for i, expense in enumerate(self._expenses_cache):
            if expense.expense_id == expense.expense_id:
                self._expenses_cache[i] = expense
                break

    async def get_expenses(self, force_reload: bool = False) -> list[Expense]:
        if not force_reload:
            return self._expenses_cache
        self.reload_cache()
        return self._expenses_cache
