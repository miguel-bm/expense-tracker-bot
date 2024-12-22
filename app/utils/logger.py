import logging
import os


def setup_logger():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("expense-tracker-bot")
    logger.setLevel(logging.INFO)

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


logger = setup_logger()
