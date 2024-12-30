import json

import pandas as pd
from pandasql import sqldf

from app.agent.tools.base import BaseTool, ResponseContext
from app.utils.logger import logger


class QueryExpenses(BaseTool):
    """Query expenses in the database by providing the SQLite query to execute. The only table available is `expenses`.

    The `expenses` table is:

    CREATE TABLE expenses (
        expense_id TEXT PRIMARY KEY,
        timestamp DATETIME,
        sender TEXT,
        cost REAL,
        concept TEXT,
        category TEXT,  -- a string like "transportation/vehicle/fuel", not an array
        details TEXT,
        payment_method TEXT CHECK (payment_method IN ('cash', 'card', 'transfer') OR payment_method IS NULL),
        input_method TEXT CHECK (input_method IN ('manual', 'bot', 'form')) DEFAULT 'bot',
        tags TEXT,      -- a string like "tag1,tag2,tag3", not an array
        metadata TEXT   -- a JSON string
    );
    """

    sql: str

    async def call(self, response_context: ResponseContext) -> str:
        expenses = await response_context.storage.get_expenses()
        df = pd.DataFrame(
            [
                {
                    **expense.model_dump(mode="json"),
                    "category": "/".join(expense.category),
                    "tags": ",".join(expense.tags) if expense.tags else None,
                    "metadata": json.dumps(expense.metadata)
                    if expense.metadata
                    else None,
                }
                for expense in expenses
            ]
        )
        try:
            result = sqldf(self.sql, {"expenses": df})
        except Exception as e:
            logger.exception(f"Error executing query: {e}")
            return f"Error executing query: {e}"
        if result is None or result.empty:
            return "No results found"
        return result.to_string()
