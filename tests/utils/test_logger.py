"""Unit tests for guardrails_api.utils.logger module."""
import unittest
import logging
from unittest.mock import patch
from guardrails_api.utils.logger import get_logger, logger


class TestLogger(unittest.TestCase):
    """Test cases for the logger module."""

    @patch.dict('os.environ', {}, clear=True)
    def test_get_logger_default_level(self):
        """Test get_logger with default log level."""
        test_logger = get_logger()
        self.assertIsInstance(test_logger, logging.Logger)
        self.assertEqual(test_logger.name, "guardrails-api")

    @patch.dict('os.environ', {'LOGLEVEL': '10'})  # DEBUG = 10
    def test_get_logger_with_custom_level(self):
        """Test get_logger with custom log level from environment."""
        test_logger = get_logger()
        self.assertIsInstance(test_logger, logging.Logger)
        self.assertEqual(test_logger.name, "guardrails-api")

    def test_logger_instance_exists(self):
        """Test that logger instance is created."""
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "guardrails-api")

    def test_logger_has_standard_methods(self):
        """Test that logger has standard logging methods."""
        self.assertTrue(hasattr(logger, 'debug'))
        self.assertTrue(hasattr(logger, 'info'))
        self.assertTrue(hasattr(logger, 'warning'))
        self.assertTrue(hasattr(logger, 'error'))
        self.assertTrue(hasattr(logger, 'critical'))

    def test_logger_methods_are_callable(self):
        """Test that logger methods are callable."""
        self.assertTrue(callable(logger.debug))
        self.assertTrue(callable(logger.info))
        self.assertTrue(callable(logger.warning))
        self.assertTrue(callable(logger.error))
        self.assertTrue(callable(logger.critical))


if __name__ == "__main__":
    unittest.main()
