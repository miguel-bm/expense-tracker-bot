import json
from dataclasses import dataclass
from typing import Any

from openai.types.chat import ChatCompletionMessageToolCall
from pydantic import BaseModel

from app.storage.expenses.base import ExpenseStorageInterface


@dataclass
class ResponseContext:
    storage: ExpenseStorageInterface


class BaseTool(BaseModel):
    async def call(self, response_context: ResponseContext) -> str:
        raise NotImplementedError("call method must be implemented by the subclass")


def get_tool_instance(
    tool_call: ChatCompletionMessageToolCall,
    tools_available: dict[str, type[BaseTool]],
) -> BaseTool:
    tool_args: dict[str, Any] = json.loads(tool_call.function.arguments)
    tool = tools_available[tool_call.function.name]
    return tool(**tool_args)
