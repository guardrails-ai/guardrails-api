"""Unit tests for guardrails_api.utils.payload_validator module."""

import unittest
from unittest.mock import patch, Mock
from guardrails_api.utils.payload_validator import validate_payload
from guardrails_api.classes.http_error import HttpError


class TestValidatePayload(unittest.TestCase):
    """Test cases for the validate_payload function."""

    @patch("guardrails_api.utils.payload_validator.guard_validator")
    def test_validate_payload_success(self, mock_validator):
        """Test successful payload validation."""
        mock_validator.iter_errors.return_value = []

        payload = {"name": "test", "validators": []}

        # Should not raise any exception
        try:
            validate_payload(payload)
        except Exception as e:
            self.fail(f"validate_payload raised an exception: {e}")

    @patch("guardrails_api.utils.payload_validator.guard_validator")
    def test_validate_payload_with_errors(self, mock_validator):
        """Test payload validation with errors."""
        # Create mock validation errors
        error1 = Mock()
        error1.json_path = "$.name"
        error1.message = "Name is required"

        error2 = Mock()
        error2.json_path = "$.validators"
        error2.message = "Must be an array"

        mock_validator.iter_errors.return_value = [error1, error2]

        payload = {"invalid": "payload"}

        with self.assertRaises(HttpError) as context:
            validate_payload(payload)

        error = context.exception
        self.assertEqual(error.status, 400)
        self.assertEqual(error.message, "BadRequest")
        self.assertIn("$.name", error.fields)
        self.assertIn("$.validators", error.fields)

    @patch("guardrails_api.utils.payload_validator.guard_validator")
    def test_validate_payload_multiple_errors_same_path(self, mock_validator):
        """Test validation with multiple errors for the same path."""
        error1 = Mock()
        error1.json_path = "$.name"
        error1.message = "Name is required"

        error2 = Mock()
        error2.json_path = "$.name"
        error2.message = "Name must be a string"

        mock_validator.iter_errors.return_value = [error1, error2]

        payload = {"name": None}

        with self.assertRaises(HttpError) as context:
            validate_payload(payload)

        error = context.exception
        self.assertEqual(len(error.fields["$.name"]), 2)
        self.assertIn("Name is required", error.fields["$.name"])
        self.assertIn("Name must be a string", error.fields["$.name"])

    @patch("guardrails_api.utils.payload_validator.remove_nones")
    @patch("guardrails_api.utils.payload_validator.guard_validator")
    def test_validate_payload_calls_remove_nones(
        self, mock_validator, mock_remove_nones
    ):
        """Test that validate_payload calls remove_nones."""
        mock_validator.iter_errors.return_value = []
        mock_remove_nones.return_value = {"cleaned": "payload"}

        payload = {"key": "value", "none_key": None}

        validate_payload(payload)

        mock_remove_nones.assert_called_once_with(payload)

    @patch("guardrails_api.utils.payload_validator.guard_validator")
    def test_validate_payload_empty_payload(self, mock_validator):
        """Test validation with empty payload."""
        error = Mock()
        error.json_path = "$"
        error.message = "Payload cannot be empty"

        mock_validator.iter_errors.return_value = [error]

        with self.assertRaises(HttpError):
            validate_payload({})

    @patch("guardrails_api.utils.payload_validator.guard_validator")
    def test_validate_payload_http_error_details(self, mock_validator):
        """Test HttpError details when validation fails."""
        error = Mock()
        error.json_path = "$.field"
        error.message = "Invalid field"

        mock_validator.iter_errors.return_value = [error]

        with self.assertRaises(HttpError) as context:
            validate_payload({"field": "invalid"})

        http_error = context.exception
        self.assertEqual(http_error.status, 400)
        self.assertEqual(http_error.message, "BadRequest")
        self.assertEqual(
            http_error.cause, "The request payload did not match the required schema."
        )
        self.assertIsNotNone(http_error.fields)


if __name__ == "__main__":
    unittest.main()
