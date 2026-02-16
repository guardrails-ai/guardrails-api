"""Unit tests for guardrails_api.utils.has_internet_connection module."""

import unittest
from unittest.mock import patch, Mock
from guardrails_api.utils.has_internet_connection import has_internet_connection


class TestHasInternetConnection(unittest.TestCase):
    """Test cases for the has_internet_connection function."""

    @patch("guardrails_api.utils.has_internet_connection.requests.get")
    def test_has_internet_connection_success(self, mock_get):
        """Test when internet connection is available."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = has_internet_connection()
        self.assertTrue(result)
        mock_get.assert_called_once_with("https://www.guardrailsai.com/")

    @patch("guardrails_api.utils.has_internet_connection.requests.get")
    def test_has_internet_connection_failure(self, mock_get):
        """Test when internet connection is not available."""
        import requests

        mock_get.side_effect = requests.ConnectionError("No connection")

        result = has_internet_connection()
        self.assertFalse(result)
        mock_get.assert_called_once_with("https://www.guardrailsai.com/")

    @patch("guardrails_api.utils.has_internet_connection.requests.get")
    def test_has_internet_connection_timeout(self, mock_get):
        """Test when request times out."""
        import requests

        mock_get.side_effect = requests.ConnectionError("Timeout")

        result = has_internet_connection()
        self.assertFalse(result)

    @patch("guardrails_api.utils.has_internet_connection.requests.get")
    def test_has_internet_connection_http_error(self, mock_get):
        """Test when HTTP error occurs during raise_for_status."""
        import requests

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        # HTTPError will propagate since only ConnectionError is caught
        with self.assertRaises(requests.HTTPError):
            has_internet_connection()


if __name__ == "__main__":
    unittest.main()
