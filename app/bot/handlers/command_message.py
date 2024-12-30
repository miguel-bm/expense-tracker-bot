from telegram import Update
from telegram.ext import ContextTypes

from app.bot.utils import filter_message, send_typing_action
from app.storage.chat.base import ChatStorageInterface
from app.utils.logger import logger


@send_typing_action
@filter_message
async def handle_command_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.info("Command message")
    assert (
        update.message and update.message.text and update.message.text.startswith("/")
    )
    command = update.message.text.split(" ")[0]
    if command == "/resetchat":
        chat_history: ChatStorageInterface = context.bot_data["chat_storage"]
        await chat_history.clear()
        context.bot_data["chat_history"] = chat_history
        await context.bot.send_message(
            chat_id=update.message.chat_id, text="Chat reset"
        )
    else:
        await context.bot.send_message(
            chat_id=update.message.chat_id, text="Command not found"
        )
