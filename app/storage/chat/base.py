from abc import ABC, abstractmethod

from openai.types.chat import ChatCompletionMessageParam


class ChatStorageInterface(ABC):
    @abstractmethod
    async def add_message(
        self, message: ChatCompletionMessageParam
    ) -> list[ChatCompletionMessageParam]:
        pass

    @abstractmethod
    async def get_messages(self) -> list[ChatCompletionMessageParam]:
        pass
