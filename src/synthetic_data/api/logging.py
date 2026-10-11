import logging


def configure_api_logging() -> logging.Logger:
    """Configure application logging for the V0.3 API."""

    logger = logging.getLogger("synthetic_data.api")

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)

    return logger