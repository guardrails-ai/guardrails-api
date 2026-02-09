"""Unit tests for guardrails_api.config module."""
import unittest
from guardrails_api import config


class TestConfig(unittest.TestCase):
    """Test cases for the config module."""

    def test_config_module_exists(self):
        """Test that config module can be imported."""
        self.assertIsNotNone(config)

    def test_config_module_docstring(self):
        """Test that config module has docstring."""
        self.assertIsNotNone(config.__doc__)

    def test_config_is_module(self):
        """Test that config is a module."""
        import types
        self.assertIsInstance(config, types.ModuleType)


if __name__ == "__main__":
    unittest.main()
