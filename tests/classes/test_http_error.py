"""Unit tests for guardrails_api.classes.http_error module."""

import unittest
from guardrails_api.classes.http_error import HttpError


class TestHttpError(unittest.TestCase):
    """Test cases for the HttpError class."""

    def test_http_error_basic_initialization(self):
        """Test HttpError initialization with status and message."""
        error = HttpError(status=404, message="Not Found")
        self.assertEqual(error.status, 404)
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.message, "Not Found")
        self.assertEqual(error.detail, "Not Found")
        self.assertIsNone(error.cause)
        self.assertIsNone(error.fields)
        self.assertIsNone(error.context)

    def test_http_error_with_cause(self):
        """Test HttpError with cause parameter."""
        error = HttpError(
            status=500,
            message="Internal Server Error",
            cause="Database connection failed",
        )
        self.assertEqual(error.status, 500)
        self.assertEqual(error.message, "Internal Server Error")
        self.assertEqual(error.cause, "Database connection failed")
        self.assertEqual(
            error.detail, "Internal Server Error :: Database connection failed"
        )

    def test_http_error_with_fields(self):
        """Test HttpError with fields parameter."""
        fields = {"email": "Invalid format", "age": "Must be positive"}
        error = HttpError(status=400, message="Validation Error", fields=fields)
        self.assertEqual(error.status, 400)
        self.assertEqual(error.fields, fields)

    def test_http_error_with_context(self):
        """Test HttpError with context parameter."""
        error = HttpError(
            status=403, message="Forbidden", context="User lacks required permissions"
        )
        self.assertEqual(error.status, 403)
        self.assertEqual(error.context, "User lacks required permissions")

    def test_http_error_to_dict_basic(self):
        """Test HttpError to_dict with basic fields."""
        error = HttpError(status=404, message="Not Found")
        result = error.to_dict()
        expected = {"status": 404, "message": "Not Found"}
        self.assertEqual(result, expected)

    def test_http_error_to_dict_with_cause(self):
        """Test HttpError to_dict including cause."""
        error = HttpError(status=500, message="Server Error", cause="Timeout")
        result = error.to_dict()
        expected = {"status": 500, "message": "Server Error", "cause": "Timeout"}
        self.assertEqual(result, expected)

    def test_http_error_to_dict_with_fields(self):
        """Test HttpError to_dict including fields."""
        fields = {"username": "Required field"}
        error = HttpError(status=400, message="Bad Request", fields=fields)
        result = error.to_dict()
        expected = {
            "status": 400,
            "message": "Bad Request",
            "fields": {"username": "Required field"},
        }
        self.assertEqual(result, expected)

    def test_http_error_to_dict_with_context(self):
        """Test HttpError to_dict including context."""
        error = HttpError(status=401, message="Unauthorized", context="Token expired")
        result = error.to_dict()
        expected = {
            "status": 401,
            "message": "Unauthorized",
            "context": "Token expired",
        }
        self.assertEqual(result, expected)

    def test_http_error_to_dict_complete(self):
        """Test HttpError to_dict with all optional parameters."""
        fields = {"field1": "error1", "field2": "error2"}
        error = HttpError(
            status=422,
            message="Unprocessable Entity",
            cause="Validation failed",
            fields=fields,
            context="Request processing",
        )
        result = error.to_dict()
        expected = {
            "status": 422,
            "message": "Unprocessable Entity",
            "cause": "Validation failed",
            "fields": fields,
            "context": "Request processing",
        }
        self.assertEqual(result, expected)

    def test_http_error_is_exception(self):
        """Test that HttpError is an Exception subclass."""
        error = HttpError(status=500, message="Error")
        self.assertIsInstance(error, Exception)

    def test_http_error_can_be_raised(self):
        """Test that HttpError can be raised as an exception."""
        with self.assertRaises(HttpError) as context:
            raise HttpError(status=400, message="Bad Request")

        self.assertEqual(context.exception.status, 400)
        self.assertEqual(context.exception.message, "Bad Request")

    def test_http_error_detail_without_cause(self):
        """Test that detail equals message when cause is None."""
        error = HttpError(status=404, message="Resource not found")
        self.assertEqual(error.detail, "Resource not found")

    def test_http_error_detail_with_cause(self):
        """Test that detail combines message and cause."""
        error = HttpError(status=500, message="Error", cause="Root cause")
        self.assertEqual(error.detail, "Error :: Root cause")


if __name__ == "__main__":
    unittest.main()
