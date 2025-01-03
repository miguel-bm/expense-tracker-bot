import json
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from gspread.auth import service_account
from requests.exceptions import ConnectionError, RequestException

from app.models.income import Income
from app.storage.incomes.base import IncomeStorageInterface
from app.utils.config import settings
from app.utils.logger import logger

SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GSpreadIncomeStorage(IncomeStorageInterface):
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

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
            timestamp=datetime.strptime(
                str(record["timestamp"]), "%d/%m/%Y %H:%M:%S"
            ).replace(tzinfo=ZoneInfo("Europe/Madrid")),
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

    def _execute_with_retry(self, operation: callable, **kargs: Any) -> Any:
        """Execute a Google Sheets operation with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                return operation(**kargs)
            except (ConnectionError, RequestException) as e:
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(
                        f"Failed to execute operation after {self.MAX_RETRIES} attempts: {e}"
                    )
                    raise
                # Try to reconnect to the sheet
                self._client = service_account(
                    settings.GOOGLE_SHEETS_CREDENTIALS, [SCOPE]
                )
                self._sheet = self._client.open_by_key(settings.EXPENSES_SHEET_ID)
                self._expenses_worksheet = self._sheet.worksheet(
                    settings.EXPENSES_SHEET_NAME
                )
                self.reload_cache()
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}), retrying in {self.RETRY_DELAY}s: {e}"
                )
                time.sleep(self.RETRY_DELAY)
            except Exception as e:
                logger.error(f"Failed to execute operation: {e}")
                raise

    def reload_cache(self) -> None:
        logger.info("Reloading incomes cache")
        records = self._execute_with_retry(
            self._incomes_worksheet.get_all_records, head=1
        )
        logger.info(f"Found {len(records)} records")
        self._incomes_cache = [self._record_to_income(record) for record in records]
        self._incomes_cache.sort(key=lambda x: x.timestamp, reverse=False)

    async def add_income(self, income: Income) -> None:
        row = self._income_to_row(income)
        self._execute_with_retry(self._incomes_worksheet.append_row, values=row)
        self._incomes_cache.append(income)
        self._incomes_cache.sort(key=lambda x: x.timestamp, reverse=False)

    async def add_incomes(self, incomes: list[Income]) -> None:
        rows = [self._income_to_row(income) for income in incomes]
        self._execute_with_retry(self._incomes_worksheet.append_rows, values=rows)
        self._incomes_cache.extend(incomes)
        self._incomes_cache.sort(key=lambda x: x.timestamp, reverse=False)

    async def update_income(self, income: Income) -> None:
        cell = self._execute_with_retry(
            self._incomes_worksheet.find, query=income.income_id, in_column=1
        )
        if not cell:
            raise ValueError(f"Income with ID {income.income_id} not found")

        range_name = f"A{cell.row}:N{cell.row}"
        updated_row = self._income_to_row(income)
        self._execute_with_retry(
            self._incomes_worksheet.update, range_name=range_name, values=[updated_row]
        )
        for i, income in enumerate(self._incomes_cache):
            if income.income_id == income.income_id:
                self._incomes_cache[i] = income
                break

    async def get_incomes(self, force_reload: bool = False) -> list[Income]:
        if not force_reload:
            return self._incomes_cache
        self.reload_cache()
        return self._incomes_cache
