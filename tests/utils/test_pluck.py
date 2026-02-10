"""Unit tests for guardrails_api.utils.pluck module."""

import unittest
from guardrails_api.utils.pluck import pluck


class TestPluck(unittest.TestCase):
    """Test cases for the pluck function."""

    def test_pluck_with_existing_keys(self):
        """Test plucking values for keys that exist in the dictionary."""
        input_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        keys = ["a", "c"]
        result = pluck(input_dict, keys)
        self.assertEqual(result, [1, 3])

    def test_pluck_with_non_existing_keys(self):
        """Test plucking values for keys that don't exist returns None."""
        input_dict = {"a": 1, "b": 2}
        keys = ["x", "y"]
        result = pluck(input_dict, keys)
        self.assertEqual(result, [None, None])

    def test_pluck_with_mixed_keys(self):
        """Test plucking with a mix of existing and non-existing keys."""
        input_dict = {"a": 1, "b": 2, "c": 3}
        keys = ["a", "x", "c"]
        result = pluck(input_dict, keys)
        self.assertEqual(result, [1, None, 3])

    def test_pluck_with_empty_keys_list(self):
        """Test pluck with an empty list of keys."""
        input_dict = {"a": 1, "b": 2}
        keys = []
        result = pluck(input_dict, keys)
        self.assertEqual(result, [])

    def test_pluck_with_empty_dict(self):
        """Test pluck with an empty dictionary."""
        input_dict = {}
        keys = ["a", "b"]
        result = pluck(input_dict, keys)
        self.assertEqual(result, [None, None])

    def test_pluck_with_none_values(self):
        """Test pluck when values in dictionary are None."""
        input_dict = {"a": None, "b": 2, "c": None}
        keys = ["a", "b", "c"]
        result = pluck(input_dict, keys)
        self.assertEqual(result, [None, 2, None])

    def test_pluck_with_complex_values(self):
        """Test pluck with complex data types as values."""
        input_dict = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "string": "text",
            "number": 42,
        }
        keys = ["list", "dict", "string", "number"]
        result = pluck(input_dict, keys)
        self.assertEqual(result, [[1, 2, 3], {"nested": "value"}, "text", 42])


if __name__ == "__main__":
    unittest.main()
