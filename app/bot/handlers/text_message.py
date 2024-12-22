from telegram import Update
from telegram.ext import ContextTypes

from app.api.routers.agent import get_agent_response
from app.utils.config import settings
from app.utils.logger import logger


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if (
        not update.effective_chat
        or update.effective_chat.id != settings.TELEGRAM_CHAT_ID
        or not update.message
        or not update.message.text
    ):
        return

    logger.info(f"Received message: {update.message.text}")

    message = update.message.text
    response = await get_agent_response(message)
    await update.message.reply_text(response)
