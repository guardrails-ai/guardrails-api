"""Unit tests for guardrails_api.utils.try_json_loads module."""
import unittest
from guardrails_api.utils.try_json_loads import try_json_loads


class TestTryJsonLoads(unittest.TestCase):
    """Test cases for the try_json_loads function."""

    def test_valid_json_string(self):
        """Test parsing a valid JSON string."""
        json_str = '{"name": "test", "value": 123}'
        result = try_json_loads(json_str)
        self.assertEqual(result, {"name": "test", "value": 123})

    def test_valid_json_array(self):
        """Test parsing a valid JSON array."""
        json_str = '[1, 2, 3, 4, 5]'
        result = try_json_loads(json_str)
        self.assertEqual(result, [1, 2, 3, 4, 5])

    def test_valid_json_nested(self):
        """Test parsing nested JSON structure."""
        json_str = '{"outer": {"inner": [1, 2, 3]}}'
        result = try_json_loads(json_str)
        self.assertEqual(result, {"outer": {"inner": [1, 2, 3]}})

    def test_invalid_json_returns_original(self):
        """Test that invalid JSON returns the original value."""
        invalid_json = "not a json string"
        result = try_json_loads(invalid_json)
        self.assertEqual(result, invalid_json)

    def test_malformed_json_returns_original(self):
        """Test that malformed JSON returns the original value."""
        malformed = '{"key": "value",}'
        result = try_json_loads(malformed)
        self.assertEqual(result, malformed)

    def test_empty_string(self):
        """Test with empty string."""
        result = try_json_loads("")
        self.assertEqual(result, "")

    def test_json_null(self):
        """Test parsing JSON null."""
        result = try_json_loads("null")
        self.assertIsNone(result)

    def test_json_boolean_true(self):
        """Test parsing JSON boolean true."""
        result = try_json_loads("true")
        self.assertTrue(result)

    def test_json_boolean_false(self):
        """Test parsing JSON boolean false."""
        result = try_json_loads("false")
        self.assertFalse(result)

    def test_json_number(self):
        """Test parsing JSON number."""
        result = try_json_loads("42")
        self.assertEqual(result, 42)

    def test_json_float(self):
        """Test parsing JSON float."""
        result = try_json_loads("3.14")
        self.assertAlmostEqual(result, 3.14)

    def test_json_string_value(self):
        """Test parsing a JSON string value."""
        result = try_json_loads('"hello world"')
        self.assertEqual(result, "hello world")

    def test_partial_json(self):
        """Test with partial/incomplete JSON."""
        partial = '{"key": '
        result = try_json_loads(partial)
        self.assertEqual(result, partial)


if __name__ == "__main__":
    unittest.main()
