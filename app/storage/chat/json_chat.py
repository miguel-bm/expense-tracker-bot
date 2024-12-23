import asyncio
import json
from pathlib import Path
from typing import List

from openai.types.chat import ChatCompletionMessageParam

from app.storage.chat.base import ChatStorageInterface


class JsonChatStorage(ChatStorageInterface):
    def __init__(self, file_path: str = "chat_history.json"):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not self.file_path.exists():
            self.file_path.write_text("[]")

    async def add_message(
        self, message: ChatCompletionMessageParam
    ) -> list[ChatCompletionMessageParam]:
        messages = await self.get_messages()
        messages.append(message)
        content_str = json.dumps(messages, indent=2)
        await asyncio.to_thread(self.file_path.write_text, content_str)
        return messages

    async def get_messages(self) -> List[ChatCompletionMessageParam]:
        content = await asyncio.to_thread(self.file_path.read_text)
        messages_data = json.loads(content)
        return messages_data
