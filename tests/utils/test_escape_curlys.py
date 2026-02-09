"""Unit tests for guardrails_api.utils.escape_curlys module."""
import unittest
from guardrails_api.utils.escape_curlys import (
    escape_curlys,
    descape_curlys,
    open_curly_token,
    close_curly_token,
)


class TestEscapeCurlys(unittest.TestCase):
    """Test cases for the escape_curlys function."""

    def test_escape_curlys_simple(self):
        """Test escaping curly braces in simple string."""
        input_str = "Hello {world}"
        result = escape_curlys(input_str)
        expected = f"Hello {open_curly_token}world{close_curly_token}"
        self.assertEqual(result, expected)

    def test_escape_curlys_multiple(self):
        """Test escaping multiple curly braces."""
        input_str = "{a} and {b} and {c}"
        result = escape_curlys(input_str)
        expected = (
            f"{open_curly_token}a{close_curly_token} and "
            f"{open_curly_token}b{close_curly_token} and "
            f"{open_curly_token}c{close_curly_token}"
        )
        self.assertEqual(result, expected)

    def test_escape_curlys_nested(self):
        """Test escaping nested curly braces."""
        input_str = "{{nested}}"
        result = escape_curlys(input_str)
        expected = (
            f"{open_curly_token}{open_curly_token}nested"
            f"{close_curly_token}{close_curly_token}"
        )
        self.assertEqual(result, expected)

    def test_escape_curlys_none(self):
        """Test escape_curlys with None input."""
        result = escape_curlys(None)
        self.assertIsNone(result)

    def test_escape_curlys_no_curlys(self):
        """Test string without curly braces."""
        input_str = "Hello world"
        result = escape_curlys(input_str)
        self.assertEqual(result, "Hello world")

    def test_escape_curlys_empty_string(self):
        """Test with empty string."""
        result = escape_curlys("")
        self.assertEqual(result, "")

    def test_escape_curlys_only_opening(self):
        """Test with only opening curly braces."""
        input_str = "Test { string"
        result = escape_curlys(input_str)
        expected = f"Test {open_curly_token} string"
        self.assertEqual(result, expected)

    def test_escape_curlys_only_closing(self):
        """Test with only closing curly braces."""
        input_str = "Test } string"
        result = escape_curlys(input_str)
        expected = f"Test {close_curly_token} string"
        self.assertEqual(result, expected)


class TestDespaceCurlys(unittest.TestCase):
    """Test cases for the descape_curlys function."""

    def test_descape_curlys_simple(self):
        """Test descaping tokens back to curly braces."""
        input_str = f"Hello {open_curly_token}world{close_curly_token}"
        result = descape_curlys(input_str)
        self.assertEqual(result, "Hello {world}")

    def test_descape_curlys_multiple(self):
        """Test descaping multiple tokens."""
        input_str = (
            f"{open_curly_token}a{close_curly_token} and "
            f"{open_curly_token}b{close_curly_token}"
        )
        result = descape_curlys(input_str)
        self.assertEqual(result, "{a} and {b}")

    def test_descape_curlys_none(self):
        """Test descape_curlys with None input."""
        result = descape_curlys(None)
        self.assertIsNone(result)

    def test_descape_curlys_no_tokens(self):
        """Test string without escape tokens."""
        input_str = "Hello world"
        result = descape_curlys(input_str)
        self.assertEqual(result, "Hello world")

    def test_descape_curlys_empty_string(self):
        """Test with empty string."""
        result = descape_curlys("")
        self.assertEqual(result, "")

    def test_roundtrip_escape_descape(self):
        """Test that escaping and descaping returns original string."""
        original = "Test {variable} with {multiple} {curlys}"
        escaped = escape_curlys(original)
        descaped = descape_curlys(escaped)
        self.assertEqual(descaped, original)

    def test_roundtrip_with_nested(self):
        """Test roundtrip with nested braces."""
        original = "{{nested}} and {simple}"
        escaped = escape_curlys(original)
        descaped = descape_curlys(escaped)
        self.assertEqual(descaped, original)


if __name__ == "__main__":
    unittest.main()
