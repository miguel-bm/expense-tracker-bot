import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.income import Income
from app.storage.google_sheets_mixin import GoogleSheetsMixin
from app.storage.incomes.base import IncomeStorageInterface
from app.utils.config import settings


class GSpreadIncomeStorage(GoogleSheetsMixin[Income], IncomeStorageInterface):
    def __init__(self):
        super().__init__(settings.INCOMES_SHEET_ID, settings.INCOMES_SHEET_NAME)

    @property
    def _item_type_name(self) -> str:
        return "income"

    def _item_to_row(self, income: Income) -> list[str | float | bool]:
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

    def _record_to_item(self, record: dict) -> Income:
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

    async def add_income(self, income: Income) -> None:
        await self.add_item(income)

    async def add_incomes(self, incomes: list[Income]) -> None:
        await self.add_items(incomes)

    async def update_income(self, income: Income) -> None:
        await self.update_item(income, "income_id")

    async def get_incomes(self, force_reload: bool = False) -> list[Income]:
        return await self.get_items(force_reload)
