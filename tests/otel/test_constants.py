"""Unit tests for guardrails_api.otel.constants module."""

import unittest
from guardrails_api.otel import constants


class TestOtelConstants(unittest.TestCase):
    """Test cases for the otel.constants module."""

    def test_none_constant_exists(self):
        """Test that the 'none' constant exists."""
        self.assertTrue(hasattr(constants, "none"))

    def test_none_constant_value(self):
        """Test that the 'none' constant has the correct value."""
        self.assertEqual(constants.none, "none")

    def test_none_constant_is_string(self):
        """Test that the 'none' constant is a string."""
        self.assertIsInstance(constants.none, str)


if __name__ == "__main__":
    unittest.main()
