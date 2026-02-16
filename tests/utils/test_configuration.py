"""Unit tests for guardrails_api.utils.configuration module."""

import unittest
import os
import tempfile
from unittest.mock import patch
from guardrails_api.utils.configuration import valid_configuration, ConfigurationError


class TestValidConfiguration(unittest.TestCase):
    """Test cases for the valid_configuration function."""

    def setUp(self):
        """Set up test environment."""
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        # Clean up temp directory
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_with_default_config_file(self, mock_postgres):
        """Test valid configuration when default config.py exists."""
        mock_postgres.return_value = False

        # Create default config.py
        config_path = os.path.join(self.temp_dir, "config.py")
        with open(config_path, "w") as f:
            f.write("# Test config")

        result = valid_configuration()
        self.assertTrue(result)

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_with_custom_config_file(self, mock_postgres):
        """Test valid configuration with custom config file path."""
        mock_postgres.return_value = False

        # Create custom config file
        custom_config = os.path.join(self.temp_dir, "custom_config.py")
        with open(custom_config, "w") as f:
            f.write("# Custom config")

        result = valid_configuration(config=custom_config)
        self.assertTrue(result)

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_with_postgres_enabled(self, mock_postgres):
        """Test valid configuration when postgres is enabled."""
        mock_postgres.return_value = True

        result = valid_configuration()
        self.assertTrue(result)

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_raises_error_without_config(self, mock_postgres):
        """Test that ConfigurationError is raised when no config is available."""
        mock_postgres.return_value = False

        with self.assertRaises(ConfigurationError) as context:
            valid_configuration()

        self.assertIn("Configuration not provided", str(context.exception))

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_with_empty_string_config(self, mock_postgres):
        """Test with empty string config parameter."""
        mock_postgres.return_value = False

        with self.assertRaises(ConfigurationError):
            valid_configuration(config="")

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_with_none_config(self, mock_postgres):
        """Test with None config parameter."""
        mock_postgres.return_value = False

        with self.assertRaises(ConfigurationError):
            valid_configuration(config=None)

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_with_non_existing_custom_config(self, mock_postgres):
        """Test with non-existing custom config file."""
        mock_postgres.return_value = False

        with self.assertRaises(ConfigurationError):
            valid_configuration(config="/non/existing/config.py")

    @patch("guardrails_api.utils.configuration.postgres_is_enabled")
    def test_valid_configuration_postgres_overrides_missing_config(self, mock_postgres):
        """Test that postgres being enabled overrides missing config files."""
        mock_postgres.return_value = True

        # No config files exist, but postgres is enabled
        result = valid_configuration(config="")
        self.assertTrue(result)


class TestConfigurationError(unittest.TestCase):
    """Test cases for ConfigurationError exception."""

    def test_configuration_error_is_exception(self):
        """Test that ConfigurationError is an Exception."""
        error = ConfigurationError("Test error")
        self.assertIsInstance(error, Exception)

    def test_configuration_error_can_be_raised(self):
        """Test that ConfigurationError can be raised."""
        with self.assertRaises(ConfigurationError) as context:
            raise ConfigurationError("Configuration missing")

        self.assertIn("Configuration missing", str(context.exception))


if __name__ == "__main__":
    unittest.main()
