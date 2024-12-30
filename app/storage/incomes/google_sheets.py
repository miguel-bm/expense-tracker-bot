import json
from datetime import datetime

from gspread.auth import service_account

from app.models.income import Income
from app.storage.incomes.base import IncomeStorageInterface
from app.utils.config import settings
from app.utils.logger import logger

SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GSpreadIncomeStorage(IncomeStorageInterface):
    def __init__(self):
        self._client = service_account(settings.GOOGLE_SHEETS_CREDENTIALS, [SCOPE])
        self._sheet = self._client.open_by_key(settings.INCOMES_SHEET_ID)
        self._incomes_worksheet = self._sheet.worksheet(settings.INCOMES_SHEET_NAME)
        self.reload_cache()

    @classmethod
    def _income_to_row(cls, income: Income) -> list[str | float | bool]:
        return [
            income.income_id,
            income.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            income.sender,
            income.value,
            income.concept,
            "/".join(income.category),
            income.details or "",
            income.payment_method or "",
            income.input_method,
            ",".join(income.tags) if income.tags else "",
            json.dumps(income.metadata) if income.metadata else "",
        ]

    @classmethod
    def _record_to_income(cls, record: dict) -> Income:
        return Income(
            income_id=str(record["income_id"]),
            timestamp=datetime.strptime(str(record["timestamp"]), "%d/%m/%Y %H:%M:%S"),
            sender=str(record["sender"]),
            value=float(record["value"]),
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
        logger.info("Reloading incomes cache")
        records = self._incomes_worksheet.get_all_records(head=1)
        logger.info(f"Found {len(records)} records")
        self._incomes_cache = [self._record_to_income(record) for record in records]
        self._incomes_cache.sort(key=lambda x: x.timestamp, reverse=True)

    async def add_income(self, income: Income) -> None:
        row = self._income_to_row(income)
        self._incomes_worksheet.append_row(row)
        self._incomes_cache.append(income)
        self._incomes_cache.sort(key=lambda x: x.timestamp, reverse=True)

    async def add_incomes(self, incomes: list[Income]) -> None:
        rows = [self._income_to_row(income) for income in incomes]
        self._incomes_worksheet.append_rows(rows)
        self._incomes_cache.extend(incomes)
        self._incomes_cache.sort(key=lambda x: x.timestamp, reverse=True)

    async def update_income(self, income: Income) -> None:
        cell = self._incomes_worksheet.find(income.income_id, in_column=1)
        if not cell:
            raise ValueError(f"Income with ID {income.income_id} not found")

        range_name = f"A{cell.row}:N{cell.row}"
        updated_row = self._income_to_row(income)
        self._incomes_worksheet.update(range_name=range_name, values=[updated_row])
        for i, income in enumerate(self._incomes_cache):
            if income.income_id == income.income_id:
                self._incomes_cache[i] = income
                break

    async def get_incomes(self, force_reload: bool = False) -> list[Income]:
        if not force_reload:
            return self._incomes_cache
        self.reload_cache()
        return self._incomes_cache
