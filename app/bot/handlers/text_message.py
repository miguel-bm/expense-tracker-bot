from telegram import Update
from telegram.ext import ContextTypes

from app.agent.service import AgentService
from app.bot.utils import escape_telegram_markdown, filter_message, send_typing_action
from app.utils.logger import logger


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
    user_mapping: dict[str, str] = context.bot_data["user_mapping"]
    username = user_mapping.get(username or "", username)
    response = await agent_service.get_text_response(update.message.text, username)
    logger.info(f"Sending response to {username}: {response}")
    await update.message.reply_text(
        escape_telegram_markdown(response), parse_mode="MarkdownV2"
    )
