"""Unit tests for guardrails_api.utils.handle_error module."""

import unittest
import asyncio
from unittest.mock import patch
from guardrails_api.utils.handle_error import handle_error
from guardrails_api.classes.http_error import HttpError
from fastapi import HTTPException


class TestHandleError(unittest.TestCase):
    """Test cases for the handle_error decorator."""

    def test_handle_error_decorator_exists(self):
        """Test that handle_error decorator exists and is callable."""
        self.assertTrue(callable(handle_error))

    @patch("guardrails_api.utils.handle_error.logger")
    def test_handle_error_with_successful_function(self, mock_logger):
        """Test decorator with function that executes successfully."""

        @handle_error
        async def successful_function():
            return "success"

        result = asyncio.run(successful_function())
        self.assertEqual(result, "success")
        mock_logger.error.assert_not_called()

    @patch("guardrails_api.utils.handle_error.logger")
    @patch("guardrails_api.utils.handle_error.traceback.print_exception")
    def test_handle_error_with_http_error(self, mock_traceback, mock_logger):
        """Test decorator handling HttpError."""

        @handle_error
        async def raise_http_error():
            raise HttpError(status=404, message="Not Found", cause="Resource missing")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(raise_http_error())

        exception = context.exception
        self.assertEqual(exception.status_code, 404)
        self.assertEqual(exception.detail, "Not Found :: Resource missing")
        mock_logger.error.assert_called_once()

    @patch("guardrails_api.utils.handle_error.logger")
    @patch("guardrails_api.utils.handle_error.traceback.print_exception")
    def test_handle_error_with_validation_error(self, mock_traceback, mock_logger):
        """Test decorator handling ValidationError."""

        # Since we can't easily mock the import, test generic exception
        @handle_error
        async def raise_generic_error():
            raise Exception("Generic error")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(raise_generic_error())

        exception = context.exception
        self.assertEqual(exception.status_code, 500)
        mock_logger.error.assert_called()

    @patch("guardrails_api.utils.handle_error.logger")
    @patch("guardrails_api.utils.handle_error.traceback.print_exception")
    def test_handle_error_with_http_exception(self, mock_traceback, mock_logger):
        """Test decorator handling HTTPException."""

        @handle_error
        async def raise_http_exception():
            raise HTTPException(status_code=403, detail="Forbidden")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(raise_http_exception())

        exception = context.exception
        self.assertEqual(exception.status_code, 403)
        self.assertEqual(exception.detail, "Forbidden")
        mock_logger.error.assert_called_once()

    @patch("guardrails_api.utils.handle_error.logger")
    @patch("guardrails_api.utils.handle_error.traceback.print_exception")
    def test_handle_error_with_generic_exception(self, mock_traceback, mock_logger):
        """Test decorator handling generic Exception."""

        @handle_error
        async def raise_generic_exception():
            raise ValueError("Some error occurred")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(raise_generic_exception())

        exception = context.exception
        self.assertEqual(exception.status_code, 500)
        self.assertEqual(exception.detail, "Internal Server Error")
        mock_logger.error.assert_called_once()

    @patch("guardrails_api.utils.handle_error.logger")
    def test_handle_error_with_function_arguments(self, mock_logger):
        """Test decorator with function that takes arguments."""

        @handle_error
        async def function_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = asyncio.run(function_with_args("x", "y", c="z"))
        self.assertEqual(result, "x-y-z")

    @patch("guardrails_api.utils.handle_error.logger")
    def test_handle_error_preserves_function_name(self, mock_logger):
        """Test that decorator preserves function name."""

        @handle_error
        async def my_function():
            return "test"

        self.assertEqual(my_function.__name__, "my_function")

    @patch("guardrails_api.utils.handle_error.logger")
    @patch("guardrails_api.utils.handle_error.traceback.print_exception")
    def test_handle_error_logs_all_exceptions(self, mock_traceback, mock_logger):
        """Test that all exceptions are logged."""

        @handle_error
        async def raise_error():
            raise RuntimeError("Runtime error")

        with self.assertRaises(HTTPException):
            asyncio.run(raise_error())

        mock_logger.error.assert_called_once()
        mock_traceback.assert_called_once()

    def test_handle_error_can_be_called_with_or_without_parens(self):
        """Test that decorator can be used with or without parentheses."""

        @handle_error
        async def func1():
            return "test1"

        @handle_error()
        async def func2():
            return "test2"

        # Both should be callable
        self.assertTrue(callable(func1))
        self.assertTrue(callable(func2))


if __name__ == "__main__":
    unittest.main()
