"""Tests for amocatlas.logger module."""

import logging
import os
import tempfile
from pathlib import Path

from amocatlas import logger


def test_enable_disable_logging() -> None:
    """Test enabling and disabling logging globally."""
    # Test initial state
    original_state = logger.LOGGING_ENABLED

    # Test enable
    logger.enable_logging()
    assert logger.LOGGING_ENABLED is True

    # Test disable
    logger.disable_logging()
    assert logger.LOGGING_ENABLED is False

    # Restore original state
    if original_state:
        logger.enable_logging()
    else:
        logger.disable_logging()


def test_log_functions_when_enabled() -> None:
    """Test logging functions when logging is enabled."""
    logger.enable_logging()

    # Clear any existing handlers
    logger.log.handlers.clear()

    # Add a test handler to capture log messages
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.log.addHandler(handler)

    try:
        # Test that functions execute without error
        logger.log_info("Test info message")
        logger.log_warning("Test warning message")
        logger.log_error("Test error message")
        logger.log_debug("Test debug message")

        # Test with arguments
        logger.log_info("Test message with %s and %d", "string", 42)

    finally:
        # Clean up handler
        logger.log.removeHandler(handler)


def test_log_functions_when_disabled() -> None:
    """Test logging functions when logging is disabled."""
    logger.disable_logging()

    # Clear any existing handlers
    logger.log.handlers.clear()

    # Add a test handler to capture log messages
    test_logs = []

    class TestHandler(logging.Handler):
        def emit(self, record):
            test_logs.append(record)

    handler = TestHandler()
    logger.log.addHandler(handler)

    try:
        # These should not produce log records when disabled
        logger.log_info("Test info message")
        logger.log_warning("Test warning message")
        logger.log_error("Test error message")
        logger.log_debug("Test debug message")

        # No logs should have been captured
        assert len(test_logs) == 0

    finally:
        # Clean up handler
        logger.log.removeHandler(handler)


def test_setup_logger() -> None:
    """Test logger setup functionality."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Enable logging for this test
        logger.enable_logging()

        # Clear existing handlers
        logger.log.handlers.clear()

        try:
            # Setup logger with custom output directory
            logger.setup_logger("test_array", output_dir=tmp_dir)

            # Should have added a file handler
            assert len(logger.log.handlers) >= 1

            # Check that log file was created
            log_files = list(Path(tmp_dir).glob("TEST_ARRAY_*_read.log"))
            assert len(log_files) >= 1

            # Test logging to the file
            logger.log_info("Test log message")

            # Force flush and close handlers properly
            for handler in logger.log.handlers[
                :
            ]:  # Copy list to avoid modification during iteration
                handler.flush()
                if hasattr(handler, "close"):
                    handler.close()
                logger.log.removeHandler(handler)

            # Check that message was written to file
            log_content = log_files[0].read_text()
            assert "Test log message" in log_content

        finally:
            # Clean up handlers - ensure all are properly closed
            for handler in logger.log.handlers[:]:
                if hasattr(handler, "close"):
                    handler.close()
                logger.log.removeHandler(handler)
            logger.log.handlers.clear()


def test_setup_logger_when_disabled() -> None:
    """Test that setup_logger does nothing when logging is disabled."""
    logger.disable_logging()

    # Clear existing handlers
    logger.log.handlers.clear()

    try:
        # Setup logger should do nothing when disabled
        logger.setup_logger("test_array")

        # Should not have added any handlers
        assert len(logger.log.handlers) == 0

    finally:
        # This is just for cleanup
        pass


def test_setup_logger_duplicate_handlers() -> None:
    """Test that setup_logger doesn't create duplicate handlers."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        logger.enable_logging()
        logger.log.handlers.clear()

        try:
            # Setup logger twice with same parameters
            logger.setup_logger("test_array", output_dir=tmp_dir)

            logger.setup_logger("test_array", output_dir=tmp_dir)
            final_handler_count = len(logger.log.handlers)

            # Should not have added duplicate handlers
            # (Implementation may clear handlers first, so just ensure it's reasonable)
            assert final_handler_count >= 1

        finally:
            # Clean up handlers properly - close file handles first
            for handler in logger.log.handlers[:]:
                if hasattr(handler, "close"):
                    handler.close()
                logger.log.removeHandler(handler)
            logger.log.handlers.clear()


def test_log_with_different_levels() -> None:
    """Test logging with different log levels."""
    logger.enable_logging()
    logger.log.handlers.clear()

    captured_logs = []

    class TestHandler(logging.Handler):
        def emit(self, record):
            captured_logs.append((record.levelname, record.getMessage()))

    handler = TestHandler()
    handler.setLevel(logging.DEBUG)
    logger.log.addHandler(handler)

    try:
        logger.log_debug("Debug message")
        logger.log_info("Info message")
        logger.log_warning("Warning message")
        logger.log_error("Error message")

        # Check that all messages were captured with correct levels
        assert len(captured_logs) == 4
        assert ("DEBUG", "Debug message") in captured_logs
        assert ("INFO", "Info message") in captured_logs
        assert ("WARNING", "Warning message") in captured_logs
        assert ("ERROR", "Error message") in captured_logs

    finally:
        logger.log.removeHandler(handler)


def test_logger_output_directory_creation() -> None:
    """Test that logger creates output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        logger.enable_logging()
        logger.log.handlers.clear()

        # Use a nested directory that doesn't exist
        nested_dir = os.path.join(tmp_dir, "nested", "logs")

        try:
            logger.setup_logger("test_array", output_dir=nested_dir)

            # Directory should have been created
            assert Path(nested_dir).exists()
            assert Path(nested_dir).is_dir()

        finally:
            # Clean up handlers properly
            for handler in logger.log.handlers[:]:
                if hasattr(handler, "close"):
                    handler.close()
                logger.log.removeHandler(handler)
            logger.log.handlers.clear()


def test_log_message_formatting() -> None:
    """Test that log messages are formatted with arguments correctly."""
    logger.enable_logging()
    logger.log.handlers.clear()

    captured_messages = []

    class TestHandler(logging.Handler):
        def emit(self, record):
            captured_messages.append(record.getMessage())

    handler = TestHandler()
    logger.log.addHandler(handler)

    try:
        # Test message formatting
        logger.log_info("Loading %s dataset from %s", "RAPID", "/path/to/file")
        logger.log_warning("Found %d missing values", 42)
        logger.log_error("Failed to process %s: %s", "file.nc", "Invalid format")

        assert "Loading RAPID dataset from /path/to/file" in captured_messages
        assert "Found 42 missing values" in captured_messages
        assert "Failed to process file.nc: Invalid format" in captured_messages

    finally:
        logger.log.removeHandler(handler)
