"""Unit tests for guardrails_api.models.guard_item module."""

import unittest
from guardrails_api.models.guard_item import GuardItem


class TestGuardItem(unittest.TestCase):
    """Test cases for the GuardItem model."""

    def test_guard_item_initialization(self):
        """Test GuardItem initialization with all parameters."""
        railspec = {"validators": ["test_validator"]}
        guard = GuardItem(
            name="test_guard",
            railspec=railspec,
            num_reasks=3,
            description="Test guard description",
        )

        self.assertEqual(guard.name, "test_guard")
        self.assertEqual(guard.railspec, railspec)
        self.assertEqual(guard.num_reasks, 3)
        self.assertEqual(guard.description, "Test guard description")

    def test_guard_item_initialization_minimal(self):
        """Test GuardItem initialization with minimal parameters."""
        railspec = {"validators": []}
        guard = GuardItem(
            name="minimal_guard", railspec=railspec, num_reasks=None, description=None
        )

        self.assertEqual(guard.name, "minimal_guard")
        self.assertEqual(guard.railspec, railspec)
        self.assertIsNone(guard.num_reasks)
        self.assertIsNone(guard.description)

    def test_guard_item_name_as_primary_key(self):
        """Test that name is set correctly as primary key."""
        railspec = {}
        guard = GuardItem(
            name="pk_test", railspec=railspec, num_reasks=0, description=""
        )

        self.assertEqual(guard.name, "pk_test")

    def test_guard_item_with_complex_railspec(self):
        """Test GuardItem with complex railspec structure."""
        railspec = {
            "validators": [
                {"name": "validator1", "params": {"key": "value"}},
                {"name": "validator2", "params": {"key2": "value2"}},
            ],
            "output_schema": {"type": "object", "properties": {}},
        }
        guard = GuardItem(
            name="complex_guard",
            railspec=railspec,
            num_reasks=5,
            description="Complex guard",
        )

        self.assertEqual(guard.railspec, railspec)
        self.assertEqual(len(guard.railspec["validators"]), 2)

    def test_guard_item_with_zero_reasks(self):
        """Test GuardItem with zero reasks."""
        guard = GuardItem(
            name="zero_reask", railspec={}, num_reasks=0, description="No reasks"
        )

        self.assertEqual(guard.num_reasks, 0)

    def test_guard_item_with_large_num_reasks(self):
        """Test GuardItem with large number of reasks."""
        guard = GuardItem(
            name="many_reasks", railspec={}, num_reasks=100, description="Many reasks"
        )

        self.assertEqual(guard.num_reasks, 100)

    def test_guard_item_with_empty_description(self):
        """Test GuardItem with empty description."""
        guard = GuardItem(name="empty_desc", railspec={}, num_reasks=1, description="")

        self.assertEqual(guard.description, "")

    def test_guard_item_with_long_description(self):
        """Test GuardItem with long description."""
        long_desc = "A" * 1000
        guard = GuardItem(
            name="long_desc", railspec={}, num_reasks=1, description=long_desc
        )

        self.assertEqual(guard.description, long_desc)
        self.assertEqual(len(guard.description), 1000)

    def test_guard_item_tablename(self):
        """Test that GuardItem has correct table name."""
        self.assertEqual(GuardItem.__tablename__, "guards")


if __name__ == "__main__":
    unittest.main()
