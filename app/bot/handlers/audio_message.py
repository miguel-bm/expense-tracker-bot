from io import BytesIO

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import ContextTypes

from app.agent.service import AgentService
from app.bot.utils import escape_telegram_markdown, filter_message, send_typing_action
from app.utils.logger import logger


@send_typing_action
@filter_message
async def handle_audio_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    # Check for either audio or voice message
    assert update.message and (update.message.audio or update.message.voice)

    from_user = update.message.from_user
    username = from_user.username if from_user else "unknown"
    logger.info(f"Received audio/voice message from {username}")

    # Get the file_id from either audio or voice message
    if update.message.audio:
        file_id = update.message.audio.file_id
    elif update.message.voice:
        file_id = update.message.voice.file_id
    else:
        logger.error("No audio or voice message found")
        return

    audio_file = await context.bot.get_file(file_id)
    openai_async_client: AsyncOpenAI = context.bot_data["openai"]

    # Download and transcribe the audio using OpenAI whisper
    audio_bytes = await audio_file.download_as_bytearray()
    audio_file_obj = BytesIO(audio_bytes)
    audio_file_obj.name = "audio.mp3"

    transcription_response = await openai_async_client.audio.transcriptions.create(
        file=audio_file_obj, model="whisper-1"
    )
    transcription = transcription_response.text
    logger.info(f"Transcribed audio from {username}: {transcription}")

    agent_service: AgentService = context.bot_data["agent_service"]
    response = await agent_service.get_text_response(transcription, username)
    logger.info(f"Sending response to {username}: {response}")
    await update.message.reply_text(
        escape_telegram_markdown(response), parse_mode="MarkdownV2"
    )
