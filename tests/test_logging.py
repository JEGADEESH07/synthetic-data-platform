"""Tests for application logging."""

import logging

from synthetic_data.logging_config import (
    configure_logging,
    get_logger,
)


def test_configure_logging_creates_log_file(tmp_path):
    """Logging configuration should create the configured log file."""

    log_file = tmp_path / "application.log"

    logger = configure_logging(log_file=log_file)

    logger.info("test log message")

    for handler in logger.handlers:
        handler.flush()

    assert log_file.exists()
    assert "test log message" in log_file.read_text(encoding="utf-8")


def test_get_logger_uses_application_namespace():
    """Child loggers should use the synthetic_data namespace."""

    logger = get_logger("pipeline")

    assert logger.name == "synthetic_data.pipeline"


def test_configure_logging_does_not_duplicate_handlers(tmp_path):
    """Repeated configuration should not add duplicate handlers."""

    log_file = tmp_path / "application.log"

    logger = configure_logging(log_file=log_file)

    handler_count = len(logger.handlers)

    configure_logging(log_file=log_file)

    assert len(logger.handlers) == handler_count


def test_logging_preserves_standard_logging_levels(tmp_path):
    """Application logging should support normal Python log levels."""

    log_file = tmp_path / "application.log"

    logger = configure_logging(
        log_file=log_file,
        level=logging.INFO,
    )

    logger.info("info message")
    logger.warning("warning message")

    for handler in logger.handlers:
        handler.flush()

    contents = log_file.read_text(encoding="utf-8")

    assert "INFO" in contents
    assert "WARNING" in contents
    assert "info message" in contents
    assert "warning message" in contents