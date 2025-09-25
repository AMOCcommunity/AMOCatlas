# amocatlas/logger.py
import datetime
import logging
from pathlib import Path

# Global logger instance (will be configured by setup_logger)
log = logging.getLogger("amocatlas")
log.setLevel(logging.DEBUG)  # capture everything; handlers filter later

# Global logging flag
# Set to True to enable logging, False to disable
LOGGING_ENABLED = True


def enable_logging():
    """Enable logging globally."""
    global LOGGING_ENABLED
    LOGGING_ENABLED = True


def disable_logging():
    """Disable logging globally."""
    global LOGGING_ENABLED
    LOGGING_ENABLED = False


def log_info(message, *args):
    """Log an info message, if logging is enabled."""
    if LOGGING_ENABLED:
        log.info(message, *args, stacklevel=2)


def log_warning(message, *args):
    """Log a warning message, if logging is enabled."""
    if LOGGING_ENABLED:
        log.warning(message, *args, stacklevel=2)


def log_error(message, *args):
    """Log an error message, if logging is enabled."""
    if LOGGING_ENABLED:
        log.error(message, *args, stacklevel=2)


def log_debug(message, *args):
    """Log a debug message, if logging is enabled."""
    if LOGGING_ENABLED:
        log.debug(message, *args, stacklevel=2)


def setup_logger(array_name: str, output_dir: str = "logs") -> None:
    """Configure the global logger to output to a file for the given array.

    Parameters
    ----------
    array_name : str
        Name of the observing array (e.g., 'move', 'rapid', etc.).
    output_dir : str
        Directory to save log files.

    """
    if not LOGGING_ENABLED:
        return
    # Resolve output directory to project root
    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H")
    log_filename = f"{array_name.upper()}_{timestamp}_read.log"
    log_path = output_path / log_filename

    # Prevent duplicate handlers in case of multiple calls
    if not any(
        isinstance(h, logging.FileHandler) and h.baseFilename == log_path
        for h in log.handlers
    ):
        file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="w")
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(funcName)s %(message)s",
            datefmt="%Y%m%dT%H%M%S",
        )
        file_handler.setFormatter(formatter)

        # Optional: console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Clear existing handlers first
        log.handlers.clear()

        log.addHandler(file_handler)
        # log.addHandler(console_handler)

        log.info(f"Logger initialized for array: {array_name}, writing to {log_path}")
