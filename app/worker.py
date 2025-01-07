from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.utils.config import settings
from app.utils.logger import logger


async def sample_job(ctx: dict[str, Any]):
    logger.info("Running sample job")
    pass
    # from datetime import datetime

    # import aiohttp

    # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # message = f"Current time: {current_time}"

    # async with aiohttp.ClientSession() as session:
    #     telegram_url = (
    #         f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    #     )
    #     params = {"chat_id": "5275855", "text": message}

    #     async with session.get(telegram_url, params=params) as response:
    #         if response.status == 200:
    #             logger.info(f"Sent Telegram message: {message}")
    #         else:
    #             logger.error(
    #                 f"Failed to send Telegram message. Status: {response.status}"
    #             )


class WorkerSettings:
    redis_settings = RedisSettings(host=settings.REDIS_HOST)
    functions = [sample_job]
    # Configure job schedules
    cron_jobs = [cron(name="sample_job", coroutine=sample_job, hour=0, second=0)]
