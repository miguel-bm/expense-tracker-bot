from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.recurrent_expenses.main import check_subscriptions


def setup_schedules(scheduler: AsyncIOScheduler) -> None:
    """
    Setup schedules for the application.
    """
    scheduler.add_job(check_subscriptions, "interval", days=1)
