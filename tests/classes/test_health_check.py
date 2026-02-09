"""Unit tests for guardrails_api.classes.health_check module."""
import unittest
from guardrails_api.classes.health_check import HealthCheck


class TestHealthCheck(unittest.TestCase):
    """Test cases for the HealthCheck class."""

    def test_health_check_initialization(self):
        """Test HealthCheck initialization with status and message."""
        health = HealthCheck(status=200, message="OK")
        self.assertEqual(health.status, 200)
        self.assertEqual(health.message, "OK")

    def test_health_check_to_dict(self):
        """Test HealthCheck to_dict conversion."""
        health = HealthCheck(status=200, message="Service is healthy")
        result = health.to_dict()
        expected = {"status": 200, "message": "Service is healthy"}
        self.assertEqual(result, expected)

    def test_health_check_unhealthy_status(self):
        """Test HealthCheck with unhealthy status."""
        health = HealthCheck(status=503, message="Service Unavailable")
        result = health.to_dict()
        expected = {"status": 503, "message": "Service Unavailable"}
        self.assertEqual(result, expected)

    def test_health_check_various_status_codes(self):
        """Test HealthCheck with various HTTP status codes."""
        test_cases = [
            (200, "OK"),
            (201, "Created"),
            (400, "Bad Request"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
        ]

        for status, message in test_cases:
            with self.subTest(status=status, message=message):
                health = HealthCheck(status=status, message=message)
                self.assertEqual(health.status, status)
                self.assertEqual(health.message, message)
                result = health.to_dict()
                self.assertEqual(result, {"status": status, "message": message})

    def test_health_check_empty_message(self):
        """Test HealthCheck with empty message."""
        health = HealthCheck(status=200, message="")
        self.assertEqual(health.message, "")
        result = health.to_dict()
        self.assertEqual(result, {"status": 200, "message": ""})

    def test_health_check_long_message(self):
        """Test HealthCheck with long message."""
        long_message = "A" * 1000
        health = HealthCheck(status=200, message=long_message)
        self.assertEqual(health.message, long_message)
        result = health.to_dict()
        self.assertEqual(result, {"status": 200, "message": long_message})


if __name__ == "__main__":
    unittest.main()
