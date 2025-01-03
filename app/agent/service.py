from datetime import datetime, timezone
from pathlib import Path

import yaml
from jinja2 import Template
from openai import AsyncOpenAI, pydantic_function_tool
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from app.agent.tools.add_expense.tool import AddExpense
from app.agent.tools.base import BaseTool, ResponseContext, get_tool_instance
from app.agent.tools.edit_expense.tool import EditExpense
from app.agent.tools.query_expenses.tool import QueryExpenses
from app.storage.chat.base import ChatStorageInterface
from app.storage.expenses.base import ExpenseStorageInterface
from app.utils.categories import get_categories_str
from app.utils.config import settings
from app.utils.logger import logger

TOOLS: list[type[BaseTool]] = [AddExpense, EditExpense, QueryExpenses]
TOOL_MAP = {str(tool_class.__name__): tool_class for tool_class in TOOLS}
CATEGORIES_PATH = "expense_categories.yml"
SPECIAL_INSTRUCTIONS_PATH = "category_instructions.txt"

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompt.jinja2"
SYSTEM_PROMPT_TEMPLATE = Template(SYSTEM_PROMPT_PATH.read_text())

SPECIAL_INSTRUCTIONS = Path(SPECIAL_INSTRUCTIONS_PATH).read_text()


class AgentService:
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        expense_storage: ExpenseStorageInterface,
        chat_storage: ChatStorageInterface,
    ):
        self.openai = openai_client
        self.expense_storage = expense_storage
        self.chat_storage = chat_storage
        self.tool_schemas = [pydantic_function_tool(tool_class) for tool_class in TOOLS]

    async def _get_system_message(
        self, response_context: ResponseContext
    ) -> ChatCompletionSystemMessageParam:
        categories: dict[str, dict | None] = yaml.safe_load(
            Path(CATEGORIES_PATH).read_text()
        )
        content = SYSTEM_PROMPT_TEMPLATE.render(
            language=settings.DEFAULT_LANGUAGE,
            currency=settings.DEFAULT_CURRENCY,
            categories=get_categories_str(categories),
            special_instructions=SPECIAL_INSTRUCTIONS,
            expenses=(await self.expense_storage.get_expenses())[-20:],
            now=datetime.now(timezone.utc),
        )
        return ChatCompletionSystemMessageParam(content=content, role="system")

    async def get_text_response(
        self,
        user_message: str,
        user_name: str | None = None,
        message_limit: int = 20,
    ) -> str:
        logger.info("Getting text response from agent")
        message = ChatCompletionUserMessageParam(role="user", content=user_message)
        if user_name:
            message["name"] = user_name

        messages = await self.chat_storage.add_message(message)
        messages = messages[-message_limit:]
        response_context = ResponseContext(storage=self.expense_storage)
        while True:
            system_message = await self._get_system_message(response_context)
            completion = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[system_message] + messages,
                tools=self.tool_schemas,
            )
            logger.info(f"Completion: {completion}")
            completion_message = completion.choices[0].message
            message_param = ChatCompletionAssistantMessageParam(
                **completion_message.model_dump(mode="json")
            )
            messages = await self.chat_storage.add_message(message_param)
            if not completion_message.tool_calls:
                logger.info(
                    f"No tool calls, returning content: {completion_message.content}"
                )
                if completion_message.content is None:
                    raise ValueError("Tool call without content")
                return completion_message.content

            tool_call = completion_message.tool_calls[0]
            logger.info(
                f"Calling tool with id {tool_call.id}: {tool_call.function.name} with args: {tool_call.function.arguments}"
            )
            tool_instance = get_tool_instance(tool_call, TOOL_MAP)

            try:
                tool_result = await tool_instance.call(response_context)
            except Exception as e:
                logger.error(f"Error calling tool {tool_call.id}: {e}")
                tool_result = f"Error calling tool {tool_call.id}: {e}"
            logger.info(f"Tool result for {tool_call.id}: {tool_result}")
            tool_message = ChatCompletionToolMessageParam(
                content=tool_result, role="tool", tool_call_id=tool_call.id
            )
            messages = await self.chat_storage.add_message(tool_message)
