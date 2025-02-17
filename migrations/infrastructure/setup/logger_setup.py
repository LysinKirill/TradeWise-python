import logging

COLORS = {
    "DEBUG": "\033[94m",  # Blue
    "INFO": "\033[92m",   # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",    # Red
    "CRITICAL": "\033[91m", # Red (bold)
    "RESET": "\033[0m",     # Reset to default color
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels."""

    def format(self, record):
        levelname = record.levelname
        colored_levelname = f"{COLORS.get(levelname, '')}{levelname}{COLORS['RESET']}"
        record.levelname = colored_levelname
        return super().format(record)

def setup_logging():
    """Configure logging with colored output."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = ColoredFormatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


if __name__ == "__main__":
    setup_logging()