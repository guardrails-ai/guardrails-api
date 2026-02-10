"""Unit tests for guardrails_api.cli.start module."""

import unittest
from guardrails_api.cli import start


class TestStartModule(unittest.TestCase):
    """Test cases for the start module."""

    def test_start_module_exists(self):
        """Test that start module can be imported."""
        self.assertIsNotNone(start)

    def test_start_module_has_start_function(self):
        """Test that start module has a start function."""
        self.assertTrue(hasattr(start, "start"))

    def test_start_function_is_callable(self):
        """Test that start function is callable."""
        self.assertTrue(callable(start.start))


if __name__ == "__main__":
    unittest.main()
