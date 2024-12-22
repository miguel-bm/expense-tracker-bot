import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from telegram.ext import Application

from app.bot import setup_handlers
from app.scheduler import setup_schedules
from app.utils.config import settings
from app.utils.logger import logger

# Configure logging
TELEGRAM_TOKEN = settings.TELEGRAM_BOT_TOKEN

# Global instances
scheduler = AsyncIOScheduler()
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()


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

    # Start scheduler
    scheduler.start()

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
        scheduler.shutdown()

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

setup_handlers(telegram_app)
setup_schedules(scheduler)

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
