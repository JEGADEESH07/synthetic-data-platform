"""Application logging configuration."""

import logging
from pathlib import Path


DEFAULT_LOG_FILE = Path("data/output/application.log")

_CONFIGURED_LOG_FILE: Path | None = None


def configure_logging(
    log_file: str | Path = DEFAULT_LOG_FILE,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure application logging."""

    global _CONFIGURED_LOG_FILE

    logger = logging.getLogger("synthetic_data")
    logger.setLevel(level)

    path = Path(log_file).resolve()

    if _CONFIGURED_LOG_FILE == path:
        logger.setLevel(level)

        for handler in logger.handlers:
            handler.setLevel(level)

        return logger

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        path,
        encoding="utf-8",
    )

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.propagate = False

    _CONFIGURED_LOG_FILE = path

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the application namespace."""

    return logging.getLogger(
        f"synthetic_data.{name}"
    )