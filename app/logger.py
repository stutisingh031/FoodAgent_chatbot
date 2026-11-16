
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Project root: parent of the app directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory where log files will be stored
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "support_agent.log"


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("food_support")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if setup runs more than once
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Write logs to a file and rotate when the file grows
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Also show logs in the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
