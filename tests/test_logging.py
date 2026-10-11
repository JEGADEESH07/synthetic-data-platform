import logging

from synthetic_data.api.logging import configure_api_logging


def test_api_logging_is_configured():
    logger = configure_api_logging()

    assert logger.name == "synthetic_data.api"
    assert logger.level == logging.INFO
    assert logger.handlers


def test_api_logging_does_not_duplicate_handlers():
    first = configure_api_logging()
    handler_count = len(first.handlers)

    second = configure_api_logging()

    assert second is first
    assert len(second.handlers) == handler_count