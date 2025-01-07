import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Awaitable, Callable

import uvicorn
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, Request, Response
from openai import AsyncOpenAI
from starlette.middleware.base import BaseHTTPMiddleware
from telegram.ext import Application

from app.agent.service import AgentService
from app.bot import setup_handlers
from app.storage.chat.json_chat import JsonChatStorage
from app.storage.expenses.google_sheets import GSpreadExpenseStorage
from app.storage.incomes.google_sheets import GSpreadIncomeStorage
from app.utils.config import settings
from app.utils.logger import logger

if settings.DEBUG:
    logger.info("Running in debug mode")


# Global instances
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
expense_storage = GSpreadExpenseStorage()
income_storage = GSpreadIncomeStorage()
chat_storage = JsonChatStorage()
agent_service = AgentService(openai_client, expense_storage, chat_storage)
telegram_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
if Path(settings.USER_MAPPING_FILE).exists():
    user_mapping = json.loads(Path(settings.USER_MAPPING_FILE).read_text())
else:
    user_mapping = {}


# Add Redis pool creation
redis_settings = RedisSettings(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    retry_on_timeout=True,
)


# Add global objects to bot data
telegram_app.bot_data["openai"] = openai_client
telegram_app.bot_data["expense_storage"] = expense_storage
telegram_app.bot_data["income_storage"] = income_storage
telegram_app.bot_data["chat_storage"] = chat_storage
telegram_app.bot_data["agent_service"] = agent_service
telegram_app.bot_data["user_mapping"] = user_mapping


# Add this new class
class StateMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Remove scheduler from state
        request.state.telegram_app = telegram_app
        request.state.expense_storage = expense_storage
        request.state.openai = openai_client
        request.state.user_mapping = user_mapping
        response = await call_next(request)
        return response


async def process_updates():
    """Process updates from the update queue"""
    async with telegram_app:
        while True:
            try:
                update = await telegram_app.update_queue.get()
                await telegram_app.process_update(update)
                telegram_app.update_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing update: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Startup
    logger.info("Starting up services...")

    # Create Redis pool instead of starting scheduler
    redis_pool = await create_pool(redis_settings)
    app.state.redis = redis_pool
    # Add Redis pool to bot_data
    telegram_app.bot_data["redis"] = redis_pool

    # Initialize telegram bot without running polling yet
    await telegram_app.initialize()

    if not telegram_app.updater:
        raise ValueError("Telegram updater not initialized")

    # Start the polling in a background task
    polling_task = asyncio.create_task(telegram_app.updater.start_polling())

    # Start update processing in a background task
    process_task = asyncio.create_task(process_updates())

    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down services...")
        await redis_pool.close()

        # Stop the polling task
        await telegram_app.updater.stop()
        await polling_task
        process_task.cancel()

        try:
            await process_task
        except asyncio.CancelledError:
            logger.info("Update processing task was cancelled")

        # Cleanup telegram bot
        if telegram_app.running:
            await telegram_app.stop()
            await telegram_app.shutdown()


# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)
app.add_middleware(StateMiddleware)

setup_handlers(telegram_app)

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
