from telegram import Update
from telegram.ext import ContextTypes

from app.utils.config import settings


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

    message = update.message.text
    await update.message.reply_text(f"I read: {message}")
