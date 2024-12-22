import logging
import os
from functools import lru_cache

# Add this near the top of the file, before setting up your own logger
logging.getLogger("httpx").setLevel(logging.WARNING)


@lru_cache(maxsize=None)
def get_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("expense-tracker-bot")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Create file handler
        fh = logging.FileHandler("logs/bot.log")
        fh.setLevel(logging.INFO)

        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Create formatter and add to handlers
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


# Export the singleton logger instance
logger = get_logger()
