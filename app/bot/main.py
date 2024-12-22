from telegram.ext import Application, MessageHandler, filters

from app.bot.handlers.text_message import handle_text_message


def setup_handlers(application: Application) -> None:
    """Setup bot handlers"""
    # Handle all messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )