from functools import wraps

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

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
        ):
            logger.info(f"Skipping message due to filter: {update.message}")
            return
        logger.info(f"Processing message: {update.message}")
        return await func(update, context, *args, **kwargs)

    return command_func


SPECIAL_CHARS = [
    "_",
    "*",
    "[",
    "]",
    "(",
    ")",
    "~",
    "`",
    ">",
    "#",
    "+",
    "-",
    "=",
    "|",
    "{",
    "}",
    ".",
    "!",
]


def escape_telegram_markdown(text: str) -> str:
    # Store the formatting patterns to preserve
    replacements = {
        "**": "BOLD",  # bold
        "`": "CODE",  # code
        "_": "ITALIC",  # italic
        "__": "UNDERLINE",  # underline
        "~~": "STRIKETHROUGH",  # strikethrough
    }

    # First, temporarily replace valid markdown entities
    # Process longer patterns first to avoid conflicts
    for pattern, placeholder in sorted(
        replacements.items(), key=lambda x: len(x[0]), reverse=True
    ):
        text = text.replace(pattern, f"§{placeholder}§")

    # Escape all special characters
    for char in SPECIAL_CHARS:
        text = text.replace(char, f"\\{char}")

    # Restore markdown entities
    format_map = {
        "§BOLD§": "*",  # bold
        "§CODE§": "`",  # code
        "§ITALIC§": "_",  # italic
        "§UNDERLINE§": "__",  # underline
        "§STRIKETHROUGH§": "~",  # strikethrough
    }

    for placeholder, markdown in format_map.items():
        text = text.replace(placeholder, markdown)

    return text
