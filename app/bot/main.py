from telegram.ext import Application, MessageHandler, filters

from app.bot.handlers.audio_message import handle_audio_message
from app.bot.handlers.command_message import handle_command_message
from app.bot.handlers.file_message import handle_file_message
from app.bot.handlers.text_message import handle_text_message


def setup_handlers(application: Application) -> None:
    application.add_handler(MessageHandler(filters.COMMAND, handle_command_message))
    application.add_handler(MessageHandler(filters.TEXT, handle_text_message))
    application.add_handler(
        MessageHandler(filters.AUDIO | filters.VOICE, handle_audio_message)
    )
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file_message))
