"""Unit tests for guardrails_api.utils.gather_request_metrics module."""
import unittest
from guardrails_api.utils.gather_request_metrics import gather_request_metrics


class TestGatherRequestMetrics(unittest.TestCase):
    """Test cases for the gather_request_metrics decorator."""

    def test_gather_request_metrics_decorator_exists(self):
        """Test that gather_request_metrics decorator exists."""
        self.assertTrue(callable(gather_request_metrics))

    def test_gather_request_metrics_returns_function_result(self):
        """Test that decorator returns the function result."""
        @gather_request_metrics
        def test_function():
            return "test_result"

        result = test_function()
        self.assertEqual(result, "test_result")

    def test_gather_request_metrics_with_arguments(self):
        """Test decorator with function that has arguments."""
        @gather_request_metrics
        def add(a, b):
            return a + b

        result = add(5, 3)
        self.assertEqual(result, 8)

    def test_gather_request_metrics_with_kwargs(self):
        """Test decorator with function that has keyword arguments."""
        @gather_request_metrics
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet("Alice", greeting="Hi")
        self.assertEqual(result, "Hi, Alice!")

    def test_gather_request_metrics_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @gather_request_metrics
        def my_function():
            return "test"

        self.assertEqual(my_function.__name__, "my_function")

    def test_gather_request_metrics_with_exception(self):
        """Test decorator behavior when function raises exception."""
        @gather_request_metrics
        def raise_error():
            raise ValueError("Test error")

        with self.assertRaises(ValueError) as context:
            raise_error()

        self.assertEqual(str(context.exception), "Test error")

    def test_gather_request_metrics_with_multiple_calls(self):
        """Test decorator with multiple function calls."""
        call_count = []

        @gather_request_metrics
        def increment():
            call_count.append(1)
            return len(call_count)

        result1 = increment()
        result2 = increment()
        result3 = increment()

        self.assertEqual(result1, 1)
        self.assertEqual(result2, 2)
        self.assertEqual(result3, 3)

    def test_gather_request_metrics_with_none_return(self):
        """Test decorator with function that returns None."""
        @gather_request_metrics
        def returns_none():
            return None

        result = returns_none()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
