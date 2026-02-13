"""Unit tests for guardrails_api.utils.remove_nones module."""

import unittest
from guardrails_api.utils.remove_nones import remove_nones


class TestRemoveNones(unittest.TestCase):
    """Test cases for the remove_nones function."""

    def test_remove_nones_simple_dict(self):
        """Test removing None values from a simple dictionary."""
        input_dict = {"a": 1, "b": None, "c": 3}
        result = remove_nones(input_dict)
        self.assertEqual(result, {"a": 1, "c": 3})

    def test_remove_nones_all_none(self):
        """Test removing None values when all values are None."""
        input_dict = {"a": None, "b": None, "c": None}
        result = remove_nones(input_dict)
        self.assertEqual(result, {})

    def test_remove_nones_no_none(self):
        """Test dictionary with no None values."""
        input_dict = {"a": 1, "b": 2, "c": 3}
        result = remove_nones(input_dict)
        self.assertEqual(result, {"a": 1, "b": 2, "c": 3})

    def test_remove_nones_empty_dict(self):
        """Test with empty dictionary."""
        input_dict = {}
        result = remove_nones(input_dict)
        self.assertEqual(result, {})

    def test_remove_nones_nested_dict(self):
        """Test removing None values from nested dictionaries."""
        input_dict = {
            "a": 1,
            "b": {"x": 2, "y": None, "z": 3},
            "c": None,
        }
        result = remove_nones(input_dict)
        self.assertEqual(result, {"a": 1, "b": {"x": 2, "z": 3}})

    def test_remove_nones_list_with_nones(self):
        """Test removing None values from lists within dictionary."""
        input_dict = {"a": [1, None, 3, None, 5], "b": 2}
        result = remove_nones(input_dict)
        self.assertEqual(result, {"a": [1, 3, 5], "b": 2})

    def test_remove_nones_list_with_dicts(self):
        """Test removing None values from list of dictionaries."""
        input_dict = {
            "items": [
                {"x": 1, "y": None},
                {"x": None, "y": 2},
                {"x": 3, "y": 4},
            ]
        }
        result = remove_nones(input_dict)
        expected = {
            "items": [
                {"x": 1},
                {"y": 2},
                {"x": 3, "y": 4},
            ]
        }
        self.assertEqual(result, expected)

    def test_remove_nones_complex_nested_structure(self):
        """Test with complex nested structure of dicts and lists."""
        input_dict = {
            "a": {
                "b": [
                    {"c": 1, "d": None},
                    None,
                    {"e": None, "f": 2},
                ],
                "g": None,
            },
            "h": None,
            "i": 3,
        }
        result = remove_nones(input_dict)
        expected = {
            "a": {
                "b": [
                    {"c": 1},
                    {"f": 2},
                ]
            },
            "i": 3,
        }
        self.assertEqual(result, expected)

    def test_remove_nones_with_zero_and_false(self):
        """Test that 0 and False are not removed (only None is removed)."""
        input_dict = {
            "zero": 0,
            "false": False,
            "none": None,
            "empty_string": "",
            "empty_list": [],
        }
        result = remove_nones(input_dict)
        expected = {
            "zero": 0,
            "false": False,
            "empty_string": "",
            "empty_list": [],
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
