"""Unit tests for guardrails_api.otel.logs module."""

import unittest
from unittest.mock import patch
from guardrails_api.otel.logs import logs_are_disabled


class TestLogsAreDisabled(unittest.TestCase):
    """Test cases for the logs_are_disabled function."""

    @patch.dict("os.environ", {}, clear=True)
    def test_logs_disabled_by_default(self):
        """Test that logs are disabled when no env var is set."""
        result = logs_are_disabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"OTEL_LOGS_EXPORTER": "none"})
    def test_logs_disabled_when_set_to_none(self):
        """Test that logs are disabled when set to 'none'."""
        result = logs_are_disabled()
        self.assertTrue(result)

    @patch.dict("os.environ", {"OTEL_LOGS_EXPORTER": "otlp"})
    def test_logs_enabled_when_set_to_otlp(self):
        """Test that logs are enabled when set to 'otlp'."""
        result = logs_are_disabled()
        self.assertFalse(result)

    @patch.dict("os.environ", {"OTEL_LOGS_EXPORTER": "console"})
    def test_logs_enabled_when_set_to_console(self):
        """Test that logs are enabled when set to 'console'."""
        result = logs_are_disabled()
        self.assertFalse(result)

    @patch.dict("os.environ", {"OTEL_LOGS_EXPORTER": ""})
    def test_logs_enabled_when_set_to_empty_string(self):
        """Test that logs are enabled when set to empty string."""
        result = logs_are_disabled()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
