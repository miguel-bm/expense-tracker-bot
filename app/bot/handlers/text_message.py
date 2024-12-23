from functools import wraps

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.agent.service import AgentService
from app.utils.config import settings
from app.utils.logger import logger


def send_typing_action(func):
    @wraps(func)
    async def command_func(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        assert update.effective_message
        await context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING
        )
        return await func(update, context, *args, **kwargs)

    return command_func


def filter_message(func):
    @wraps(func)
    async def command_func(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        if (
            not update.effective_chat
            or update.effective_chat.id != settings.TELEGRAM_CHAT_ID
            or not update.message
            or not update.message.text
        ):
            return
        return await func(update, context, *args, **kwargs)

    return command_func


@send_typing_action
@filter_message
async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    assert update.message and update.message.text

    from_user = update.message.from_user
    username = from_user.username if from_user else "unknown"
    logger.info(f"Received message from {username}: {update.message.text}")
    agent_service: AgentService = context.bot_data["agent_service"]
    response = await agent_service.get_text_response(update.message.text, username)
    logger.info(f"Sending response to {username}: {response}")
    await update.message.reply_text(response)
