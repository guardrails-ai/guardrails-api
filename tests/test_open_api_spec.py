"""Unit tests for guardrails_api.open_api_spec module."""

import unittest
from unittest.mock import patch, mock_open
from guardrails_api import open_api_spec


class TestGetOpenApiSpec(unittest.TestCase):
    """Test cases for the get_open_api_spec function."""

    def setUp(self):
        """Reset global variable before each test."""
        open_api_spec.open_api_spec = None

    @patch("builtins.open", new_callable=mock_open, read_data='{"version": "1.0"}')
    @patch("os.path.abspath")
    @patch("os.path.join")
    @patch("os.path.dirname")
    def test_get_open_api_spec_loads_file(
        self, mock_dirname, mock_join, mock_abspath, mock_file
    ):
        """Test that get_open_api_spec loads the JSON file."""
        mock_dirname.return_value = "/app/guardrails_api"
        mock_join.return_value = "/app/guardrails_api/open-api-spec.json"
        mock_abspath.return_value = "/app/guardrails_api/open-api-spec.json"

        result = open_api_spec.get_open_api_spec()

        self.assertEqual(result, {"version": "1.0"})
        mock_file.assert_called_once_with("/app/guardrails_api/open-api-spec.json")

    @patch("builtins.open", new_callable=mock_open, read_data='{"openapi": "3.0.0"}')
    @patch("os.path.abspath")
    @patch("os.path.join")
    @patch("os.path.dirname")
    def test_get_open_api_spec_caches_result(
        self, mock_dirname, mock_join, mock_abspath, mock_file
    ):
        """Test that get_open_api_spec caches the result."""
        mock_dirname.return_value = "/app/guardrails_api"
        mock_join.return_value = "/app/guardrails_api/open-api-spec.json"
        mock_abspath.return_value = "/app/guardrails_api/open-api-spec.json"

        # First call
        result1 = open_api_spec.get_open_api_spec()
        # Second call
        result2 = open_api_spec.get_open_api_spec()

        self.assertEqual(result1, result2)
        self.assertEqual(result1, {"openapi": "3.0.0"})
        # File should only be opened once due to caching
        mock_file.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data='{"paths": {}}')
    @patch("os.path.abspath")
    @patch("os.path.join")
    @patch("os.path.dirname")
    def test_get_open_api_spec_returns_dict(
        self, mock_dirname, mock_join, mock_abspath, mock_file
    ):
        """Test that get_open_api_spec returns a dictionary."""
        mock_dirname.return_value = "/app"
        mock_join.return_value = "/app/open-api-spec.json"
        mock_abspath.return_value = "/app/open-api-spec.json"

        result = open_api_spec.get_open_api_spec()

        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
