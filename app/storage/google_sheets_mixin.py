import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from gspread.auth import service_account
from requests.exceptions import ConnectionError, RequestException

from app.utils.config import settings
from app.utils.logger import logger

T = TypeVar("T")  # This will be either Expense or Income

SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GoogleSheetsMixin(Generic[T], ABC):
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self, sheet_id: str, worksheet_name: str):
        self._client = service_account(settings.GOOGLE_SHEETS_CREDENTIALS, [SCOPE])
        self._sheet = self._client.open_by_key(sheet_id)
        self._worksheet = self._sheet.worksheet(worksheet_name)
        self._cache: list[T] = []
        self.reload_cache()

    @abstractmethod
    def _item_to_row(self, item: T) -> list[str | float | bool]:
        """Convert an item to a row format for Google Sheets"""
        pass

    @abstractmethod
    def _record_to_item(self, record: dict) -> T:
        """Convert a Google Sheets record to an item"""
        pass

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
                self._worksheet = self._sheet.worksheet(settings.EXPENSES_SHEET_NAME)
                self.reload_cache()
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}), retrying in {self.RETRY_DELAY}s: {e}"
                )
                time.sleep(self.RETRY_DELAY)
            except Exception as e:
                logger.error(f"Failed to execute operation: {e}")
                raise

    async def add_item(self, item: T) -> None:
        row = self._item_to_row(item)
        self._execute_with_retry(self._worksheet.append_row, values=row)
        self._cache.append(item)
        self._cache.sort(key=lambda x: x.timestamp, reverse=False)  # type: ignore

    async def add_items(self, items: list[T]) -> None:
        rows = [self._item_to_row(item) for item in items]
        self._execute_with_retry(self._worksheet.append_rows, values=rows)
        self._cache.extend(items)
        self._cache.sort(key=lambda x: x.timestamp, reverse=False)  # type: ignore

    async def update_item(self, item: T, id_field: str) -> None:
        item_id = getattr(item, id_field)
        cell = self._execute_with_retry(
            self._worksheet.find, query=item_id, in_column=1
        )
        if not cell:
            raise ValueError(f"{id_field} with ID {item_id} not found")

        range_name = f"A{cell.row}:N{cell.row}"
        updated_row = self._item_to_row(item)
        self._execute_with_retry(
            self._worksheet.update, range_name=range_name, values=[updated_row]
        )
        for i, cached_item in enumerate(self._cache):
            if getattr(cached_item, id_field) == item_id:
                self._cache[i] = item
                break

    async def get_items(self, force_reload: bool = False) -> list[T]:
        if not force_reload:
            return self._cache
        self.reload_cache()
        return self._cache

    def reload_cache(self) -> None:
        logger.info("Reloading cache")
        records = self._execute_with_retry(self._worksheet.get_all_records, head=1)
        logger.info(f"Found {len(records)} records")
        self._cache = [self._record_to_item(record) for record in records]
        self._cache.sort(key=lambda x: x.timestamp, reverse=False)  # type: ignore
