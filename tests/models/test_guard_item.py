"""Unit tests for guardrails_api.models.guard_item module."""

import unittest
from guardrails_api.db.models.guard_item import GuardItem


class TestGuardItem(unittest.TestCase):
    """Test cases for the GuardItem model."""

    def test_guard_item_initialization(self):
        """Test GuardItem initialization with all parameters."""
        guard_dict = {"validators": ["test_validator"]}
        guard = GuardItem(name="test_guard", guard=guard_dict)

        self.assertEqual(guard.name, "test_guard")
        self.assertEqual(guard.guard, guard_dict)

    def test_guard_item_initialization_minimal(self):
        """Test GuardItem initialization with minimal parameters."""
        guard_dict = {"validators": []}
        guard = GuardItem(name="minimal_guard", guard=guard_dict)

        self.assertEqual(guard.name, "minimal_guard")
        self.assertEqual(guard.guard, guard_dict)

    def test_guard_item_name_as_primary_key(self):
        """Test that name is set correctly as primary key."""
        guard_dict = {}
        guard = GuardItem(name="pk_test", guard=guard_dict)

        self.assertEqual(guard.name, "pk_test")

    def test_guard_item_with_complex_guard(self):
        """Test GuardItem with complex guard structure."""
        guard_dict = {
            "validators": [
                {"name": "validator1", "params": {"key": "value"}},
                {"name": "validator2", "params": {"key2": "value2"}},
            ],
            "output_schema": {"type": "object", "properties": {}},
        }
        guard = GuardItem(name="complex_guard", guard=guard_dict)

        self.assertEqual(guard.guard, guard_dict)
        self.assertEqual(len(guard.guard["validators"]), 2)

    def test_guard_item_tablename(self):
        """Test that GuardItem has correct table name."""
        self.assertEqual(GuardItem.__tablename__, "guards")


if __name__ == "__main__":
    unittest.main()
